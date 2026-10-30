import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config.cache_conf import close_redis
from .config.db_conf import engine
from .routers.favorite import router as favorite_router
from .routers.history import router as history_router
from .routers.news import router as news_router
from .routers.users import router as users_router
from .utils.response import ApiResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="AI掘金头条新闻系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)
app.include_router(news_router)
app.include_router(favorite_router)
app.include_router(history_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(
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
