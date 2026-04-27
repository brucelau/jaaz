import sys
import io
from contextlib import asynccontextmanager
from fastapi import FastAPI

from web.services.log_service import app_logger as logger
from web.services.config_service import config_service
from web.services.tool_service import tool_service
from web.websocket.emitter import broadcast_init_done


async def initialize():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    logger.info("startup", msg="initializing_config_service")
    await config_service.initialize()
    logger.info("startup", msg="initializing_broadcast_init_done")
    await broadcast_init_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize()
    await tool_service.initialize()
    yield
