import logging

from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from toutiao_backend.utils.error_handlers import register_exception_handlers


def create_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/http-error")
    async def http_error() -> None:
        raise HTTPException(status_code=404, detail="资源不存在")

    @app.get("/validation-error")
    async def validation_error(page: int) -> dict[str, int]:
        return {"page": page}

    @app.get("/unhandled-error")
    async def unhandled_error() -> None:
        raise RuntimeError("boom")

    return app


async def get(app: FastAPI, path: str):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.get(path)


async def test_http_exception_handler_returns_unified_envelope() -> None:
    # Arrange
    app = create_test_app()

    # Act
    response = await get(app, "/http-error")

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "code": 404,
        "message": "资源不存在",
        "data": None,
    }


async def test_validation_exception_handler_returns_unified_envelope() -> None:
    # Arrange
    app = create_test_app()

    # Act
    response = await get(app, "/validation-error?page=invalid")

    # Assert
    assert response.status_code == 422
    assert response.json() == {
        "code": 422,
        "message": "请求参数校验失败",
        "data": None,
    }


async def test_unhandled_exception_handler_logs_and_returns_server_error(
    caplog,
) -> None:
    # Arrange
    app = create_test_app()

    # Act
    with caplog.at_level(
        logging.ERROR,
        logger="toutiao_backend.utils.error_handlers",
    ):
        response = await get(app, "/unhandled-error")

    # Assert
    assert response.status_code == 500
    assert response.json() == {
        "code": 500,
        "message": "服务器内部错误",
        "data": None,
    }
    records = [
        record
        for record in caplog.records
        if record.name == "toutiao_backend.utils.error_handlers"
    ]
    assert len(records) == 1
    assert records[0].message == "Unhandled error: GET /unhandled-error"
    assert records[0].exc_info is not None
