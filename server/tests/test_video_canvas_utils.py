import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestVideoCanvasUtilsImports:
    def test_canvas_lock_manager_exists(self):
        from tools.video_generation.video_canvas_utils import CanvasLockManager
        assert CanvasLockManager is not None

    def test_canvas_lock_manager_has_lock_method(self):
        from tools.video_generation.video_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        assert hasattr(manager, 'lock_canvas')

    def test_canvas_lock_manager_has_locks_dict(self):
        from tools.video_generation.video_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        assert hasattr(manager, '_locks')
        assert manager._locks == {}


class TestCanvasLockManager:
    @pytest.mark.asyncio
    async def test_creates_lock_for_new_canvas(self):
        from tools.video_generation.video_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        async with manager.lock_canvas('canvas_1'):
            assert 'canvas_1' in manager._locks

    @pytest.mark.asyncio
    async def test_reuses_existing_lock(self):
        from tools.video_generation.video_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        async with manager.lock_canvas('canvas_1'):
            lock1 = manager._locks['canvas_1']
        async with manager.lock_canvas('canvas_1'):
            lock2 = manager._locks['canvas_1']
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_different_canvases_have_different_locks(self):
        from tools.video_generation.video_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        async with manager.lock_canvas('canvas_1'):
            lock1 = manager._locks['canvas_1']
        async with manager.lock_canvas('canvas_2'):
            lock2 = manager._locks['canvas_2']
        assert lock1 is not lock2


class TestVideoCanvasUtilsFunctions:
    def test_save_video_to_canvas_function_exists(self):
        from tools.video_generation.video_canvas_utils import save_video_to_canvas
        assert callable(save_video_to_canvas)
