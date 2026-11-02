from __future__ import annotations

import asyncio
import gzip
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx

from nonfunctional.config import (
    NEWS_COUNT,
    PERFORMANCE_PASSWORD,
    PROJECT_ROOT,
    TEST_DATABASE,
    TEST_REDIS_DB,
    USER_COUNT,
    artifact_root,
    configure_test_environment,
    performance_token,
)


@dataclass(frozen=True)
class Service:
    name: str
    process: subprocess.Popen | None
    url: str


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _find_port(start: int) -> int:
    for port in range(start, start + 100):
        if _port_is_free(port):
            return port
    raise RuntimeError("No free local port found.")


def _wait_http(url: str, process: subprocess.Popen, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    with httpx.Client(timeout=1) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    f"Service exited with code {process.returncode}: {url}"
                )
            try:
                if client.get(url).status_code < 500:
                    return
            except Exception:
                pass
            time.sleep(0.25)
    raise TimeoutError(f"Service did not become ready: {url}")


def _start(
    command: list[str], name: str, env: dict[str, str]
) -> tuple[subprocess.Popen, Path]:
    log_path = artifact_root() / f"{name}.log"
    log_file = log_path.open("a", encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )
    return process, log_path


def _stop(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def npm_command(*args: str) -> list[str]:
    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_cmd is None:
        raise FileNotFoundError("npm executable not found on PATH")
    if npm_cmd.lower().endswith(".cmd"):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", npm_cmd, *args]
    return [npm_cmd, *args]


def build_frontend() -> None:
    env = os.environ.copy()
    result = subprocess.run(
        npm_command("run", "build"),
        cwd=PROJECT_ROOT / "toutiao_frontend",
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    log_path = artifact_root() / "frontend-build.log"
    log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Frontend build failed; see {log_path}")


def package_sizes() -> dict[str, object]:
    assets = PROJECT_ROOT / "toutiao_frontend" / "dist" / "assets"
    js = list(assets.glob("*.js"))
    css = list(assets.glob("*.css"))
    uncompressed_js = sum(path.stat().st_size for path in js)
    gzip_js = sum(len(gzip.compress(path.read_bytes(), compresslevel=9)) for path in js)
    payload = {
        "files": len(js) + len(css),
        "js_files": len(js),
        "css_files": len(css),
        "js_uncompressed_bytes": uncompressed_js,
        "js_gzip_bytes": gzip_js,
        "js_gzip_kib": round(gzip_js / 1024, 1),
    }
    (artifact_root() / "frontend-bundle.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def start_services() -> tuple[Service, Service]:
    configure_test_environment()
    env = os.environ.copy()
    env["MYSQL_DATABASE"] = TEST_DATABASE
    env["REDIS_DB"] = str(TEST_REDIS_DB)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    api_port = _find_port(8140)
    api_url = f"http://127.0.0.1:{api_port}"
    api_command = [
        sys.executable,
        "-m",
        "uvicorn",
        "toutiao_backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(api_port),
        "--workers",
        "1",
        "--log-level",
        "warning",
    ]
    api_process, api_log = _start(api_command, "e2e-api", env)

    web_port = _find_port(8150)
    web_url = f"http://127.0.0.1:{web_port}"
    web_command = [
        sys.executable,
        "-m",
        "nonfunctional.frontend_server",
        "--directory",
        str(PROJECT_ROOT / "toutiao_frontend" / "dist"),
        "--api-url",
        api_url,
        "--port",
        str(web_port),
    ]
    web_process, web_log = _start(web_command, "e2e-web", env)
    try:
        _wait_http(f"{api_url}/openapi.json", api_process)
        _wait_http(web_url, web_process)
    except Exception:
        _stop(api_process)
        _stop(web_process)
        raise
    return (
        Service(name="api", process=api_process, url=api_url),
        Service(name="web", process=web_process, url=web_url),
    )


def stop_services(services: tuple[Service, ...]) -> None:
    for service in reversed(services):
        _stop(service.process)
