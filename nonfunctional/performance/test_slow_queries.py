from __future__ import annotations

import re

import pytest
from sqlalchemy import text

from nonfunctional.artifacts import write_json
from nonfunctional.dataset import token_for_user
from toutiao_backend.config.db_conf import engine

pytestmark = [pytest.mark.nonfunctional]


def _plan_queries() -> dict[str, str]:
    token = token_for_user(1)
    return {
        "news_list": (
            "SELECT id FROM news WHERE category_id = 1 "
            "ORDER BY publish_time DESC, id DESC LIMIT 10 OFFSET 0"
        ),
        "news_detail": "SELECT * FROM news WHERE id = 9999",
        "related_news": (
            "SELECT n.id FROM related_news r JOIN news n "
            "ON n.id = r.related_news_id WHERE r.news_id = 9999 "
            "ORDER BY n.publish_time DESC, n.id DESC"
        ),
        "auth_token": (
            "SELECT u.id FROM user u JOIN user_token t ON u.id = t.user_id "
            f"WHERE t.token = '{token}' AND t.expires_at > NOW()"
        ),
        "favorite_list": (
            "SELECT f.id, n.id FROM favorite f JOIN news n "
            "ON n.id = f.news_id WHERE f.user_id = 1 "
            "ORDER BY f.created_at DESC, f.id DESC LIMIT 10 OFFSET 0"
        ),
        "history_list": (
            "SELECT h.id, n.id FROM history h JOIN news n "
            "ON n.id = h.news_id WHERE h.user_id = 1 "
            "ORDER BY h.view_time DESC, h.id DESC"
        ),
    }


def _actual_ms(plan: str) -> float:
    matches = re.findall(r"actual time=[\d.]+\.\.([\d.]+)", plan)
    return max((float(value) for value in matches), default=0.0)


async def test_hot_queries_do_not_use_full_table_scans() -> None:
    results: dict[str, dict[str, object]] = {}
    async with engine.connect() as connection:
        for name, query in _plan_queries().items():
            result = await connection.execute(text(f"EXPLAIN ANALYZE {query}"))
            plan = "\n".join(str(row[0]) for row in result)
            results[name] = {
                "max_actual_ms": _actual_ms(plan),
                "has_table_scan": "Table scan" in plan,
                "has_filesort": "Sort:" in plan,
                "plan": plan,
            }

    write_json("slow-query-plans.json", results)

    scanned = [name for name, result in results.items() if result["has_table_scan"]]
    assert not scanned, f"Full table scans found in hot queries: {scanned}"
