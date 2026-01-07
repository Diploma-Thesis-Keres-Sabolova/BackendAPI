from fastapi import FastAPI
from app.api import raw_data, providers, runs
import os
import logging
from dotenv import load_dotenv
from app.database import engine
from app.utils.logger_config import LoggerConfigurator
from app.utils.middleware import RequestIdMiddleware
from contextlib import asynccontextmanager

load_dotenv()
ENV = os.getenv("ENV", "development")

config = LoggerConfigurator(
    name="BackendAPI",
    level=logging.INFO,
    logfile="logs/myapp.log",
    when="midnight",
    backup_count=30,
    use_json=True,
)
config.configure_root_logger()

logger = logging.getLogger("BackendAPI")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Fast API opened")
    yield
    engine.dispose()
    logger.info("Fast API closed")

app = FastAPI(
    root_path=os.getenv("FATS_API_ROOT_PATH", "/api"),
    lifespan=lifespan,
    openapi_url="/openapi.json" if ENV != "production" else None,
    docs_url="/docs" if ENV != "production" else None,
    redoc_url="/redoc" if ENV != "production" else None,
)

app.add_middleware(RequestIdMiddleware, header_name="X-Request-ID")

app.include_router(providers.router)
app.include_router(runs.router)
app.include_router(raw_data.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
