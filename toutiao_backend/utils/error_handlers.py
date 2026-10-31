import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .response import ApiResponse

logger = logging.getLogger(__name__)


async def _http_exception_handler(
    _: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "请求失败"
    response = ApiResponse[None](
        code=exc.status_code,
        message=message,
        data=None,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


async def _validation_exception_handler(
    _: Request,
    __: RequestValidationError,
) -> JSONResponse:
    response = ApiResponse[None](
        code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        message="请求参数校验失败",
        data=None,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump(mode="json"),
    )


async def _unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled error: %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    response = ApiResponse[None](
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="服务器内部错误",
        data=None,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        _validation_exception_handler,
    )
    app.add_exception_handler(Exception, _unhandled_exception_handler)
