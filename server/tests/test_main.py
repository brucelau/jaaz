import pytest


class TestMainAppCreation:
    def test_no_cache_static_files_is_subclass(self):
        from core.static import NoCacheStaticFiles
        from starlette.staticfiles import StaticFiles
        assert issubclass(NoCacheStaticFiles, StaticFiles)

    def test_png_endpoint_defined(self):
        from main import app
        route_paths = [route.path for route in app.routes]
        assert any('{filename}' in path and '.png' in path for path in route_paths)
