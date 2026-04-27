import pytest


class TestFindNextBestElementPosition:
    @pytest.mark.asyncio
    async def test_returns_zero_zero_when_no_elements(self):
        from agents.tools.utils.canvas import find_next_best_element_position
        canvas_data = {"elements": []}
        x, y = await find_next_best_element_position(canvas_data)
        assert x == 0
        assert y == 0

    @pytest.mark.asyncio
    async def test_returns_zero_zero_when_no_media_elements(self):
        from agents.tools.utils.canvas import find_next_best_element_position
        canvas_data = {"elements": [{"type": "text", "x": 10, "y": 10}]}
        x, y = await find_next_best_element_position(canvas_data)
        assert x == 0
        assert y == 0

    @pytest.mark.asyncio
    async def test_single_element_returns_next_to_it(self):
        from agents.tools.utils.canvas import find_next_best_element_position
        canvas_data = {
            "elements": [
                {"type": "image", "x": 0, "y": 0, "width": 100, "height": 100, "isDeleted": False}
            ]
        }
        x, y = await find_next_best_element_position(canvas_data, max_num_per_row=4, spacing=20)
        assert x == 120  # 0 + 100 + 20
        assert y == 0

    @pytest.mark.asyncio
    async def test_new_row_when_row_full(self):
        from agents.tools.utils.canvas import find_next_best_element_position
        canvas_data = {
            "elements": [
                {"type": "image", "x": 0, "y": 0, "width": 100, "height": 100, "isDeleted": False},
                {"type": "image", "x": 120, "y": 0, "width": 100, "height": 100, "isDeleted": False},
                {"type": "image", "x": 240, "y": 0, "width": 100, "height": 100, "isDeleted": False},
                {"type": "image", "x": 360, "y": 0, "width": 100, "height": 100, "isDeleted": False},
            ]
        }
        x, y = await find_next_best_element_position(canvas_data, max_num_per_row=4, spacing=20)
        assert x == 0
        assert y == 120  # 0 + 100 + 20

    @pytest.mark.asyncio
    async def test_skips_deleted_elements(self):
        from agents.tools.utils.canvas import find_next_best_element_position
        canvas_data = {
            "elements": [
                {"type": "image", "x": 0, "y": 0, "width": 100, "height": 100, "isDeleted": True}
            ]
        }
        x, y = await find_next_best_element_position(canvas_data)
        assert x == 0
        assert y == 0

    @pytest.mark.asyncio
    async def test_skips_non_media_elements(self):
        from agents.tools.utils.canvas import find_next_best_element_position
        canvas_data = {
            "elements": [
                {"type": "text", "x": 0, "y": 0, "width": 100, "height": 100},
                {"type": "image", "x": 100, "y": 0, "width": 100, "height": 100, "isDeleted": False}
            ]
        }
        x, y = await find_next_best_element_position(canvas_data, max_num_per_row=4, spacing=20)
        assert x == 220  # 100 + 100 + 20
        assert y == 0
