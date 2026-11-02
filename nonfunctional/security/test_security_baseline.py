from __future__ import annotations

import asyncio

import pytest

from nonfunctional.dataset import token_for_user

pytestmark = [pytest.mark.nonfunctional]


async def test_responses_include_baseline_security_headers(api_client) -> None:
    response = await api_client.get("/api/news/categories")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") in {"DENY", "SAMEORIGIN"}
    assert response.headers.get("referrer-policy")


async def test_cors_does_not_allow_arbitrary_origins(api_client) -> None:
    headers = {"Origin": "https://attacker.example"}
    response = await api_client.get("/api/news/categories", headers=headers)
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin is None or allow_origin != "*"

    preflight = await api_client.options(
        "/api/news/list",
        headers={
            **headers,
            "Access-Control-Request-Method": "GET",
        },
    )
    allow_origin = preflight.headers.get("access-control-allow-origin")
    assert allow_origin is None or allow_origin != "*"


async def test_login_is_rate_limited_after_repeated_failures(api_client) -> None:
    statuses: list[int] = []
    for _ in range(10):
        response = await api_client.post(
            "/api/user/login",
            json={
                "username": "rate_limit_probe",
                "password": "wrong-password",
            },
        )
        statuses.append(response.status_code)
        await asyncio.sleep(0.02)

    assert statuses[:9] == [401] * 9
    assert statuses[9] == 429
    assert "retry-after" in response.headers


async def test_oversized_profile_payload_is_rejected(api_client) -> None:
    response = await api_client.put(
        "/api/user/update",
        headers={"Authorization": token_for_user(50)},
        json={"nickname": "x" * 300_000},
    )
    assert response.status_code in {413, 422}


async def test_sql_injection_payloads_do_not_cause_server_errors(api_client) -> None:
    category_response = await api_client.get(
        "/api/news/list",
        params={"categoryId": "1 OR 1=1", "page": 1, "pageSize": 10},
    )
    login_response = await api_client.post(
        "/api/user/login",
        json={
            "username": "' OR 1=1 -- ",
            "password": "anything",
        },
    )

    assert category_response.status_code == 422
    assert login_response.status_code in {401, 422}
    assert category_response.status_code < 500
    assert login_response.status_code < 500
