from __future__ import annotations

import random

from locust import HttpUser, between, task

from nonfunctional.dataset import token_for_user

PUBLIC_REQUESTS = (
    lambda client: client.get("/api/news/categories", name="GET /api/news/categories"),
    lambda client: client.get("/api/news/list", params={"categoryId": 1, "page": 1, "pageSize": 10}, name="GET /api/news/list"),
    lambda client: client.get("/api/news/detail", params={"id": 9000}, name="GET /api/news/detail"),
)
AUTH_READS = (
    lambda client, headers: client.get("/api/user/info", headers=headers, name="GET /api/user/info"),
    lambda client, headers: client.get("/api/favorite/list", headers=headers, params={"page": 1, "pageSize": 10}, name="GET /api/favorite/list"),
    lambda client, headers: client.get("/api/history/list", headers=headers, params={"page": 1, "pageSize": 10}, name="GET /api/history/list"),
)


class MixedNewsUser(HttpUser):
    wait_time = between(0.05, 0.15)

    def on_start(self) -> None:
        self.user_auth = {"Authorization": token_for_user(10)}
        self.user_b_auth = {"Authorization": token_for_user(11)}

    @task(35)
    def public_read(self) -> None:
        random.choice(PUBLIC_REQUESTS)(self.client)

    @task(15)
    def authenticated_read(self) -> None:
        random.choice(AUTH_READS)(self.client, self.user_auth)

    @task(3)
    def write_favorite(self) -> None:
        news_id = 8_900 + random.randint(1, 20)
        with self.client.post(
            "/api/favorite/add",
            headers=self.user_auth,
            json={"newsId": news_id},
            name="POST /api/favorite/add",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")

    @task(3)
    def write_history(self) -> None:
        news_id = 8_900 + random.randint(1, 20)
        with self.client.post(
            "/api/history/add",
            headers=self.user_auth,
            json={"newsId": news_id},
            name="POST /api/history/add",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")

    @task(4)
    def enforce_user_isolation(self) -> None:
        with self.client.get(
            "/api/user/info",
            headers=self.user_b_auth,
            name="GET /api/user/info",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
            elif response.json().get("data", {}).get("username") != "perf_user_11":
                response.failure("User identity leaked across tokens")
