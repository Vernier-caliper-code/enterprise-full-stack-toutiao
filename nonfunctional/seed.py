from __future__ import annotations

import argparse
import asyncio
import json

from nonfunctional.config import configure_test_environment

configure_test_environment()

from toutiao_backend.config.db_conf import engine
from nonfunctional.dataset import cleanup_database, prepare_and_seed, verify_seed


async def _run(command: str) -> dict[str, int] | None:
    if command == "prepare":
        return await prepare_and_seed()
    if command == "verify":
        return await verify_seed()
    if command == "cleanup":
        await cleanup_database()
        return None
    raise ValueError(f"Unknown command: {command}")


def main() -> None:
    configure_test_environment()
    parser = argparse.ArgumentParser(description="Manage isolated non-functional data.")
    parser.add_argument("command", choices=("prepare", "verify", "cleanup"))
    args = parser.parse_args()
    try:
        result = asyncio.run(_run(args.command))
    finally:
        asyncio.run(engine.dispose())
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

