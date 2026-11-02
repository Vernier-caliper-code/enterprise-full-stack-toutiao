from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time

import httpx
from redis.asyncio import Redis

from nonfunctional.artifacts import write_json
from nonfunctional.config import PROJECT_ROOT, TEST_REDIS_DB, artifact_root, configure_test_environment
from nonfunctional.dataset import cleanup_database, prepare_and_seed
from nonfunctional.performance.summary import (
    aggregate_runs,
    read_locust_stats,
    summarize_run,
    write_performance_summary,
)
from nonfunctional.server_utils import running_server
from toutiao_backend.config.cache_conf import REDIS_HOST, REDIS_PORT


def _redis_client() -> Redis:
    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=TEST_REDIS_DB,
        decode_responses=True,
        protocol=2,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


async def _flush_redis() -> None:
    client = _redis_client()
    try:
        await client.flushdb()
    finally:
        await client.aclose()


def _locust_csv(server_url: str, index: int, *, quick: bool) -> dict[str, float | int]:
    output_dir = artifact_root() / "load"
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / f"{'quick' if quick else 'run'}-{index}"
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(PROJECT_ROOT / "nonfunctional" / "performance" / "locustfile.py"),
        "--headless",
        "--host",
        server_url,
        "--users",
        "5" if quick else "20",
        "--spawn-rate",
        "1" if quick else "2",
        "--run-time",
        "10s" if quick else "60s",
        "--csv",
        str(prefix),
        "--only-summary",
        "--exit-code-on-error",
        "1",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=40 if quick else 120,
    )
    console_path = output_dir / f"{prefix.name}-console.txt"
    console_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Locust run failed; see {console_path}")
    return summarize_run(read_locust_stats(prefix))


async def _cold_cache_probes(server_url: str) -> list[dict[str, float | int | str]]:
    probes = [
        ("categories", "/api/news/categories", {}),
        ("news_list", "/api/news/list", {"categoryId": 1, "page": 1, "pageSize": 10}),
        ("news_detail", "/api/news/detail", {"id": 9_001}),
    ]
    results = []
    async with httpx.AsyncClient(base_url=server_url, timeout=10) as client:
        for name, path, params in probes:
            await _flush_redis()
            started = time.perf_counter()
            response = await client.get(path, params=params)
            elapsed_ms = (time.perf_counter() - started) * 1_000
            results.append({"name": name, "status": response.status_code, "elapsed_ms": elapsed_ms})
    write_json("cold-cache.json", results)
    return results


def _warm_up(server_url: str) -> None:
    with httpx.Client(base_url=server_url, timeout=10) as client:
        for _ in range(5):
            client.get("/api/news/categories")
            client.get("/api/news/list", params={"categoryId": 1, "page": 1, "pageSize": 10})
            client.get("/api/news/detail", params={"id": 9_000})
            client.get("/api/user/info", headers={"Authorization": "perf-token-10-" + ("x" * 40)})


async def run(quick: bool, port: int) -> dict[str, object]:
    runs = []
    with running_server(port, name="performance-server") as server:
        _warm_up(server.url)
        for index in range(1, 4):
            runs.append(_locust_csv(server.url, index, quick=quick))
        cold_cache = await _cold_cache_probes(server.url)
        await _flush_redis()

    thresholds = {"public_p95_ms": 300.0, "auth_p95_ms": 800.0, "read_p95_ms": 500.0, "error_rate": 0.01}
    aggregate = aggregate_runs(runs)
    payload = write_performance_summary(runs, aggregate, cold_cache, thresholds)
    if any(item["status"] != 200 or item["elapsed_ms"] > 500 for item in cold_cache):
        payload["passed"] = False
        write_json("performance-summary.json", payload)
    return payload


async def main_async(quick: bool, port: int) -> dict[str, object]:
    try:
        await prepare_and_seed()
        return await run(quick, port)
    finally:
        await cleanup_database()


def main() -> None:
    configure_test_environment()
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--port", type=int, default=8130)
    args = parser.parse_args()
    result = asyncio.run(main_async(args.quick, args.port))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()

