import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from core.lifespan import lifespan
from core.routers import register_routers
from core.static import setup_static_files
from core.config import setup_proxy_bypass
from web.websocket.manager import sio
from web.services.log_service import app_logger as logger

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_routers(app)
setup_static_files(app)

sio_app = socketio.ASGIApp(sio)
app.mount("/socket.io", sio_app)

if __name__ == "__main__":
    setup_proxy_bypass()

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=57988, help='Port to run the server on')
    args = parser.parse_args()

    import uvicorn
    logger.info("startup", msg="starting_server", port=args.port, ui_dist_dir=__import__('os').environ.get('UI_DIST_DIR'))
    uvicorn.run(app, host="127.0.0.1", port=args.port)
