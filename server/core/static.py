import os
from fastapi import FastAPI, Response
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


def get_react_build_dir():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.environ.get('UI_DIST_DIR', os.path.join(root_dir, "react", "dist"))


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


def setup_static_files(app: FastAPI):
    react_build_dir = get_react_build_dir()

    static_site = os.path.join(react_build_dir, "assets")
    if os.path.exists(static_site):
        app.mount("/assets", NoCacheStaticFiles(directory=static_site), name="assets")

    @app.get("/")
    async def serve_react_app():
        response = FileResponse(os.path.join(react_build_dir, "index.html"))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/{filename}.png")
    async def serve_png_files(filename: str):
        png_path = os.path.join(react_build_dir, f"{filename}.png")
        if os.path.exists(png_path):
            response = FileResponse(png_path)
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response
        return Response(status_code=404)