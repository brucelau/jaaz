import argparse

from fastapi import FastAPI
import socketio

from core.lifespan import lifespan
from core.routers import register_routers
from core.static import setup_static_files
from core.config import setup_proxy_bypass
from ws_manager.manager import sio
from services.log_service import app_logger as logger

app = FastAPI(lifespan=lifespan)
register_routers(app)
setup_static_files(app)

logger.info("startup", msg="creating_socketio_app")
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path='/socket.io')

if __name__ == "__main__":
    setup_proxy_bypass()

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=57988, help='Port to run the server on')
    args = parser.parse_args()

    import uvicorn
    logger.info("startup", msg="starting_server", port=args.port, ui_dist_dir=__import__('os').environ.get('UI_DIST_DIR'))
    uvicorn.run(socket_app, host="127.0.0.1", port=args.port)
