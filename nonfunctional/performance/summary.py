from __future__ import annotations

import csv
import statistics
from pathlib import Path

from nonfunctional.artifacts import write_json

PUBLIC_ENDPOINTS = {
    "GET /api/news/categories",
    "GET /api/news/list",
    "GET /api/news/detail",
}
AUTH_ENDPOINTS = {
    "GET /api/user/info",
    "GET /api/favorite/list",
    "GET /api/history/list",
}


def read_locust_stats(csv_prefix: Path) -> dict[str, dict[str, float]]:
    stats_path = Path(f"{csv_prefix}_stats.csv")
    with stats_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    result: dict[str, dict[str, float]] = {}
    for row in rows:
        name = row["Name"]
        if not name or name == "Aggregated":
            continue
        result[name] = {
            "requests": float(row["Request Count"]),
            "failures": float(row["Failure Count"]),
            "p50_ms": float(row["50%"]),
            "p95_ms": float(row["95%"]),
            "p99_ms": float(row["99%"]),
            "avg_ms": float(row["Average Response Time"]),
        }
    return result


def summarize_run(stats: dict[str, dict[str, float]]) -> dict[str, float | int]:
    public = {name: row for name, row in stats.items() if name in PUBLIC_ENDPOINTS}
    auth = {name: row for name, row in stats.items() if name in AUTH_ENDPOINTS}
    all_rows = list(stats.values())
    reads = public | auth
    return {
        "requests": int(sum(row["requests"] for row in all_rows)),
        "failures": int(sum(row["failures"] for row in all_rows)),
        "public_p95_ms": max((row["p95_ms"] for row in public.values()), default=0.0),
        "auth_p95_ms": max((row["p95_ms"] for row in auth.values()), default=0.0),
        "read_p95_ms": max((row["p95_ms"] for row in reads.values()), default=0.0),
        "error_rate": (
            sum(row["failures"] for row in all_rows)
            / max(1, sum(row["requests"] for row in all_rows))
        ),
    }


def aggregate_runs(runs: list[dict[str, float | int]]) -> dict[str, float | int]:
    return {
        "runs": len(runs),
        "public_p95_ms": statistics.median(run["public_p95_ms"] for run in runs),
        "auth_p95_ms": statistics.median(run["auth_p95_ms"] for run in runs),
        "read_p95_ms": statistics.median(run["read_p95_ms"] for run in runs),
        "error_rate": statistics.median(run["error_rate"] for run in runs),
        "requests_total": int(sum(run["requests"] for run in runs)),
        "failures_total": int(sum(run["failures"] for run in runs)),
    }


def write_performance_summary(
    run_metrics: list[dict[str, float | int]],
    aggregate: dict[str, float | int],
    cold_cache: list[dict[str, float | int | str]],
    thresholds: dict[str, float],
) -> dict[str, object]:
    passed = (
        aggregate["public_p95_ms"] <= thresholds["public_p95_ms"]
        and aggregate["auth_p95_ms"] <= thresholds["auth_p95_ms"]
        and aggregate["error_rate"] < thresholds["error_rate"]
    )
    payload = {
        "passed": passed,
        "thresholds": thresholds,
        "runs": run_metrics,
        "aggregate": aggregate,
        "cold_cache": cold_cache,
    }
    write_json("performance-summary.json", payload)
    return payload

