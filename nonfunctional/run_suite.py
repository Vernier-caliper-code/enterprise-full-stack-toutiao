from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass

from nonfunctional.artifacts import write_json
from nonfunctional.config import (
    PROJECT_ROOT,
    TEST_DATABASE,
    TEST_REDIS_DB,
    artifact_root,
    configure_test_environment,
)
from nonfunctional.dataset import cleanup_database, prepare_and_seed
from nonfunctional.e2e_services import npm_command


@dataclass
class Stage:
    name: str
    command: list[str]
    timeout: int = 1800


def _python(*args: str) -> list[str]:
    return [sys.executable, *args]


def _npm(*args: str) -> list[str]:
    return npm_command(*args)


def _run_stage(stage: Stage) -> dict[str, object]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["MYSQL_DATABASE"] = TEST_DATABASE
    env["REDIS_DB"] = str(TEST_REDIS_DB)
    result = subprocess.run(
        stage.command,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=stage.timeout,
    )
    elapsed = round(time.perf_counter() - started, 2)
    log_path = artifact_root() / f"stage-{stage.name}.log"
    log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    print(f"[{stage.name}] exit={result.returncode} elapsed={elapsed}s", flush=True)
    return {
        "name": stage.name,
        "command": stage.command,
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "elapsed_seconds": elapsed,
        "log": log_path.name,
    }


def build_stages(full: bool) -> list[Stage]:
    return [
        Stage("regression", _python("-m", "pytest", "tests", "-q")),
        Stage("frontend-build", _npm("--prefix", str(PROJECT_ROOT / "toutiao_frontend"), "run", "build")),
        Stage(
            "backend-nonfunctional",
            _python(
                "-m",
                "pytest",
                "nonfunctional",
                "-m",
                "nonfunctional",
                "-v",
                "--junitxml",
                str(artifact_root() / "backend-junit.xml"),
            ),
        ),
        Stage("security-scans", _python("-m", "nonfunctional.security.run_scans")),
        Stage(
            "performance",
            _python(
                "-m",
                "nonfunctional.performance.run",
                *([] if full else ["--quick"]),
            ),
        ),
        Stage("frontend-quality", _python("-m", "nonfunctional.frontend.run")),
        Stage("report", _python("-m", "nonfunctional.write_report")),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    configure_test_environment()
    started = time.perf_counter()
    stages: list[dict[str, object]] = []
    error = None
    try:
        asyncio.run(prepare_and_seed())
        for stage in build_stages(not args.quick):
            try:
                stages.append(_run_stage(stage))
            except Exception as exc:
                stages.append({"name": stage.name, "passed": False, "error": str(exc)})
    except Exception as exc:
        error = str(exc)
    finally:
        try:
            asyncio.run(cleanup_database())
        except Exception as exc:
            stages.append({"name": "cleanup", "passed": False, "error": str(exc)})

    summary = {
        "passed": error is None and all(stage.get("passed", False) for stage in stages),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "stages": stages,
    }
    if error:
        summary["error"] = error
    write_json("suite-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()

