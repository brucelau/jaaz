import pytest


class TestComfyDynamicPythonType:
    def test_python_type_number_int(self):
        from agents.tools.comfy_dynamic import _python_type
        assert _python_type("number", 42) == int

    def test_python_type_number_float(self):
        from agents.tools.comfy_dynamic import _python_type
        assert _python_type("number", 3.14) == float

    def test_python_type_boolean(self):
        from agents.tools.comfy_dynamic import _python_type
        assert _python_type("boolean", True) == bool
        assert _python_type("bool", False) == bool

    def test_python_type_string(self):
        from agents.tools.comfy_dynamic import _python_type
        assert _python_type("string", "default") == str
        assert _python_type("image", None) == str
        assert _python_type("file", None) == str
        assert _python_type("path", None) == str


class TestComfyDynamicBuildInputSchema:
    def test_build_input_schema_parses_list(self):
        from agents.tools.comfy_dynamic import _build_input_schema
        wf = {
            'name': 'Test Workflow',
            'inputs': [
                {'name': 'prompt', 'type': 'string', 'description': 'Enter prompt', 'required': True},
                {'name': 'steps', 'type': 'number', 'default_value': 20, 'required': False}
            ]
        }
        model = _build_input_schema(wf)
        assert model is not None
        fields = model.model_fields
        assert 'prompt' in fields
        assert 'steps' in fields

    def test_build_input_schema_handles_invalid_json(self):
        from agents.tools.comfy_dynamic import _build_input_schema
        wf = {
            'name': 'Test',
            'inputs': 'not a list'
        }
        model = _build_input_schema(wf)
        assert model is not None

    def test_build_input_schema_always_has_tool_call_id(self):
        from agents.tools.comfy_dynamic import _build_input_schema
        wf = {
            'name': 'Test',
            'inputs': []
        }
        model = _build_input_schema(wf)
        assert 'tool_call_id' in model.model_fields

    def test_build_input_schema_required_field(self):
        from agents.tools.comfy_dynamic import _build_input_schema
        wf = {
            'name': 'Test',
            'inputs': [
                {'name': 'prompt', 'type': 'string', 'required': True, 'description': 'Required prompt'}
            ]
        }
        model = _build_input_schema(wf)
        assert 'prompt' in model.model_fields

    def test_build_input_schema_optional_field(self):
        from agents.tools.comfy_dynamic import _build_input_schema
        wf = {
            'name': 'Test',
            'inputs': [
                {'name': 'seed', 'type': 'number', 'required': False, 'default_value': 42, 'description': 'Seed'}
            ]
        }
        model = _build_input_schema(wf)
        assert 'seed' in model.model_fields


class TestBuildTool:
    def test_build_tool_returns_base_tool(self):
        from agents.tools.comfy_dynamic import build_tool
        wf = {
            'id': 1,
            'name': 'Test Workflow',
            'description': 'Test workflow description',
            'inputs': [
                {'Name': 'prompt', 'type': 'string', 'description': 'Enter prompt', 'required': True}
            ]
        }
        tool = build_tool(wf)
        assert tool is not None
        assert hasattr(tool, 'name')
        assert tool.name == 'Test Workflow'
