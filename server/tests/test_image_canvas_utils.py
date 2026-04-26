import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestImageCanvasUtilsImports:
    def test_generate_file_id_exists(self):
        from tools.utils.image_canvas_utils import generate_file_id
        assert callable(generate_file_id)

    def test_canvas_lock_manager_exists(self):
        from tools.utils.image_canvas_utils import CanvasLockManager
        assert CanvasLockManager is not None

    def test_canvas_lock_manager_has_lock_method(self):
        from tools.utils.image_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        assert hasattr(manager, 'lock_canvas')


class TestGenerateFileId:
    def test_generates_id_with_prefix(self):
        from tools.utils.image_canvas_utils import generate_file_id
        file_id = generate_file_id()
        assert file_id.startswith('im_')

    def test_generates_unique_ids(self):
        from tools.utils.image_canvas_utils import generate_file_id
        ids = [generate_file_id() for _ in range(10)]
        assert len(set(ids)) == 10


class TestCanvasLockManager:
    @pytest.mark.asyncio
    async def test_creates_lock_for_new_canvas(self):
        from tools.utils.image_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        async with manager.lock_canvas('canvas_1'):
            assert 'canvas_1' in manager._locks

    @pytest.mark.asyncio
    async def test_reuses_existing_lock(self):
        from tools.utils.image_canvas_utils import CanvasLockManager
        manager = CanvasLockManager()
        async with manager.lock_canvas('canvas_1'):
            lock1 = manager._locks['canvas_1']
        async with manager.lock_canvas('canvas_1'):
            lock2 = manager._locks['canvas_1']
        assert lock1 is lock2


class TestGenerateNewImageElement:
    @pytest.mark.asyncio
    async def test_generate_new_image_element_function_exists(self):
        from tools.utils.image_canvas_utils import generate_new_image_element
        assert callable(generate_new_image_element)
