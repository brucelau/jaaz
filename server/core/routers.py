from fastapi import FastAPI

from routers.root_router import router as root_router
from routers.config_router import router as config_router
from routers.image_router import router as image_router
from routers.workspace_router import router as workspace_router
from routers.canvas_router import router as canvas_router
from routers.chat_router import router as chat_router
from routers.settings_router import router as settings_router
from routers.tool_confirmation_router import router as tool_confirmation_router
from routers.ssl_test_router import router as ssl_test_router
from routers.auth_router import router as auth_router


def register_routers(app: FastAPI):
    app.include_router(root_router)
    app.include_router(config_router)
    app.include_router(image_router)
    app.include_router(workspace_router)
    app.include_router(canvas_router)
    app.include_router(chat_router)
    app.include_router(settings_router)
    app.include_router(tool_confirmation_router)
    app.include_router(ssl_test_router)
    app.include_router(auth_router)
