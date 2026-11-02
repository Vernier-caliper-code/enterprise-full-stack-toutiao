from __future__ import annotations

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx

from .config import PROJECT_ROOT, TEST_DATABASE, TEST_REDIS_DB, artifact_root


@dataclass(frozen=True)
class RunningServer:
    url: str
    process: subprocess.Popen


def _wait_until_ready(url: str, process: subprocess.Popen, timeout: float = 20) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    with httpx.Client(timeout=1) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Server exited with code {process.returncode}.")
            try:
                response = client.get(f"{url}/openapi.json")
                if response.status_code == 200:
                    return
            except Exception as exc:  # pragma: no cover - diagnostic path
                last_error = exc
            time.sleep(0.2)
    raise TimeoutError(f"Server did not become ready: {last_error}")


@contextmanager
def running_server(
    port: int,
    *,
    redis_port: int = 6379,
    mysql_port: int | None = None,
    name: str = "server",
) -> Iterator[RunningServer]:
    env = os.environ.copy()
    env["MYSQL_DATABASE"] = TEST_DATABASE
    env["REDIS_DB"] = str(TEST_REDIS_DB)
    env["REDIS_HOST"] = "127.0.0.1"
    env["REDIS_PORT"] = str(redis_port)
    if mysql_port is not None:
        env["MYSQL_PORT"] = str(mysql_port)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    log_path = artifact_root() / f"{name}.log"
    log_file = Path(log_path).open("a", encoding="utf-8")
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "toutiao_backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "1",
            "--log-level",
            "warning",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    url = f"http://127.0.0.1:{port}"

    try:
        _wait_until_ready(url, process)
        yield RunningServer(url=url, process=process)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_file.close()
