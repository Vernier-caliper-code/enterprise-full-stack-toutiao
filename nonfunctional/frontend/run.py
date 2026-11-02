from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from nonfunctional.artifacts import write_json
from nonfunctional.config import (
    PROJECT_ROOT,
    TEST_DATABASE,
    TEST_REDIS_DB,
    artifact_root,
    configure_test_environment,
)
from nonfunctional.e2e_services import (
    build_frontend,
    npm_command,
    package_sizes,
    start_services,
    stop_services,
)

FRONTEND_ROOT = PROJECT_ROOT / "nonfunctional" / "frontend"


def _write_services(api_url: str, web_url: str) -> Path:
    path = FRONTEND_ROOT / "services.json"
    path.write_text(
        json.dumps(
            {
                "web": web_url,
                "api": api_url,
                "database": TEST_DATABASE,
                "redis_db": TEST_REDIS_DB,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _prepare_data() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "nonfunctional.seed", "prepare"],
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(PROJECT_ROOT),
            "MYSQL_DATABASE": TEST_DATABASE,
            "REDIS_DB": str(TEST_REDIS_DB),
        },
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Could not prepare browser test fixture: " + result.stdout + result.stderr
        )


def _run_browser_tests() -> dict[str, object]:
    _prepare_data()
    services = start_services()
    _write_services(services[0].url, services[1].url)
    result = None
    try:
        result = subprocess.run(
            npm_command("run", "test:nonfunctional"),
            cwd=PROJECT_ROOT / "toutiao_frontend",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=900,
        )
    finally:
        stop_services(services)
    assert result is not None
    log_path = artifact_root() / "frontend-quality.log"
    log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    return {
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "log": log_path.name,
    }


def _bundle_has_secret() -> bool:
    assets = PROJECT_ROOT / "toutiao_frontend" / "dist" / "assets"
    pattern = re.compile(r"sk-[A-Za-z0-9_-]{16,}")
    return any(
        pattern.search(path.read_text(encoding="utf-8", errors="ignore"))
        for path in assets.glob("*.js")
    )


def main() -> None:
    configure_test_environment()
    build_frontend()
    report = {
        "build": {"passed": True},
        "bundle": package_sizes(),
        "production_bundle_has_secret": _bundle_has_secret(),
    }
    report["quality"] = _run_browser_tests()
    report["passed"] = (
        report["build"]["passed"]
        and not report["production_bundle_has_secret"]
        and report["quality"]["passed"]
    )
    write_json("frontend-summary.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
