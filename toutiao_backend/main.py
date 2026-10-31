from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config.cache_conf import close_redis
from .config.db_conf import engine
from .routers.favorite import router as favorite_router
from .routers.history import router as history_router
from .routers.news import router as news_router
from .routers.users import router as users_router
from .utils.error_handlers import register_exception_handlers


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

register_exception_handlers(app)

app.include_router(users_router)
app.include_router(news_router)
app.include_router(favorite_router)
app.include_router(history_router)
