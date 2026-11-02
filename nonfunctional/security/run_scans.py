from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from nonfunctional.artifacts import write_json
from nonfunctional.config import PROJECT_ROOT, artifact_root
from nonfunctional.e2e_services import npm_command

TEST_SECRET_PATHS = {
    "nonfunctional/config.py",
    "nonfunctional/conftest.py",
    "nonfunctional/reliability/test_concurrency.py",
    "nonfunctional/security/test_security_baseline.py",
    "tests/unit/test_security.py",
    "nonfunctional/.secrets.baseline",
    ".pytest_cache/CACHEDIR.TAG",

}


def _run(command: list[str], name: str, cwd: Path = PROJECT_ROOT) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    log_path = artifact_root() / f"{name}.log"
    log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    return {"command": command, "returncode": result.returncode, "log": log_path.name}


def _python_audit() -> dict[str, object]:
    output = artifact_root() / "pip-audit.json"
    result = _run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            "requirements.txt",
            "--format",
            "json",
            "--output",
            str(output),
        ],
        "pip-audit",
    )
    try:
        report = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report = []
    dependencies = (
        report.get("dependencies", []) if isinstance(report, dict) else report
    )
    result["vulnerabilities"] = [
        {
            "name": item.get("name"),
            "version": item.get("version"),
            "id": finding.get("id"),
        }
        for item in dependencies
        if isinstance(item, dict)
        for finding in item.get("vulns", [])
    ]
    return result


def _bandit() -> dict[str, object]:
    output = artifact_root() / "bandit.json"
    result = _run(
        [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            "toutiao_backend",
            "-ll",
            "-f",
            "json",
            "-o",
            str(output),
        ],
        "bandit",
    )
    try:
        report = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report = {"results": []}
    result["high_count"] = sum(
        item.get("issue_severity") == "HIGH" for item in report.get("results", [])
    )
    return result


def _secret_scan() -> dict[str, object]:
    excludes = r"nonfunctional[\\/]artifacts|node_modules|dist|\.venv|\.git|\.pytest_cache"
    result = _run(
        [
            sys.executable,
            "-m",
            "detect_secrets",
            "scan",
            "--all-files",
            "--exclude-files",
            excludes,
        ],
        "detect-secrets",
    )
    try:
        report = json.loads(
            (artifact_root() / "detect-secrets.log").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        report = {"results": {}}
    hits = [
        {
            "file": filename.replace("\\", "/"),
            "line": item.get("line_number"),
            "type": item.get("type"),
        }
        for filename, items in report.get("results", {}).items()
        for item in items
    ]
    actionable = [item for item in hits if item["file"] not in TEST_SECRET_PATHS]
    return {
        "passed": not actionable and result["returncode"] == 0,
        "hits": actionable,
        **result,
    }


def _production_bundle_scan() -> dict[str, object]:
    bundle = PROJECT_ROOT / "toutiao_frontend" / "dist" / "assets"
    pattern = re.compile(r"sk-[A-Za-z0-9_-]{16,}")
    hits = []
    if bundle.exists():
        for path in bundle.glob("*.js"):
            if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                hits.append({"file": path.name, "type": "provider_api_key"})
    return {"passed": not hits, "hits": hits}


def _npm_audit() -> dict[str, object]:
    result = _run(
        npm_command("audit", "--registry=https://registry.npmjs.org", "--json"),
        "npm-audit",
        cwd=PROJECT_ROOT / "toutiao_frontend",
    )
    try:
        report = json.loads(
            (artifact_root() / "npm-audit.log").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        report = {"metadata": {"vulnerabilities": {"high": 1, "critical": 1}}}
    counts = report.get("metadata", {}).get("vulnerabilities", {})
    return {
        "passed": counts.get("high", 0) == 0 and counts.get("critical", 0) == 0,
        "counts": counts,
        **result,
    }


def main() -> None:
    pip_audit = _python_audit()
    bandit = _bandit()
    secrets = _secret_scan()
    bundle = _production_bundle_scan()
    npm_audit = _npm_audit()
    report = {
        "passed": (
            not pip_audit.get("vulnerabilities")
            and bandit.get("high_count", 0) == 0
            and secrets.get("passed", False)
            and bundle.get("passed", False)
            and npm_audit.get("passed", False)
        ),
        "pip_audit": pip_audit,
        "bandit": bandit,
        "secrets": secrets,
        "production_bundle": bundle,
        "npm_audit": npm_audit,
    }
    write_json("security-scan.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()

