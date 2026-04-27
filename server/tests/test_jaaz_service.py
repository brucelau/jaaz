import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from contextlib import asynccontextmanager


class TestJaazServiceInit:
    def test_jaaz_service_requires_api_url(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': '', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            with pytest.raises(ValueError, match="Jaaz API URL is not configured"):
                JaazService()

    def test_jaaz_service_requires_api_token(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': ''}}
            from web.services.jaaz_service import JaazService
            with pytest.raises(ValueError, match="Jaaz API token is not configured"):
                JaazService()

    def test_jaaz_service_appends_api_v1(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            service = JaazService()
            assert service.api_url == 'https://api.test.com/api/v1'


class TestJaazServiceHelpers:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    def test_is_configured_returns_true_when_valid(self, jaaz_service):
        assert jaaz_service.is_configured() is True

    def test_build_headers(self, jaaz_service):
        headers = jaaz_service._build_headers()
        assert headers['Authorization'] == 'Bearer test_key'
        assert headers['Content-Type'] == 'application/json'


def make_mock_response(status, json_data=None, text_data=None):
    mock_response = MagicMock()
    mock_response.status = status
    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)
    if text_data is not None:
        mock_response.text = AsyncMock(return_value=text_data)
    return mock_response


def make_mock_session(post_response=None, get_response=None):
    mock_session = MagicMock()
    if post_response:
        mock_post_context = MagicMock()
        mock_post_context.__aenter__ = AsyncMock(return_value=post_response)
        mock_post_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post_context)
    if get_response:
        mock_get_context = MagicMock()
        mock_get_context.__aenter__ = AsyncMock(return_value=get_response)
        mock_get_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_get_context)
    return mock_session


def make_mock_create_aiohttp(mock_session):
    @asynccontextmanager
    async def mock_create_aiohttp(*args, **kwargs):
        yield mock_session
    return mock_create_aiohttp


class TestCreateMagicTask:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    @pytest.mark.asyncio
    async def test_returns_empty_for_invalid_image_format(self, jaaz_service):
        result = await jaaz_service.create_magic_task("not_image_data")
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_content(self, jaaz_service):
        result = await jaaz_service.create_magic_task("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_task_id_on_success(self, jaaz_service):
        mock_response = make_mock_response(200, json_data={'task_id': 'task_123'})
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            result = await jaaz_service.create_magic_task("data:image/png;base64,abc123")
            assert result == "task_123"

    @pytest.mark.asyncio
    async def test_returns_empty_on_failure(self, jaaz_service):
        mock_response = make_mock_response(500, text_data='Internal Error')
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            result = await jaaz_service.create_magic_task("data:image/png;base64,abc123")
            assert result == ""


class TestCreateVideoTask:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    @pytest.mark.asyncio
    async def test_raises_exception_on_failure(self, jaaz_service):
        mock_response = make_mock_response(400, text_data='Bad Request')
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            with pytest.raises(Exception, match="Failed to create video task"):
                await jaaz_service.create_video_task(prompt="test", model="seedance")

    @pytest.mark.asyncio
    async def test_raises_exception_when_no_task_id(self, jaaz_service):
        mock_response = make_mock_response(200, json_data={})
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            with pytest.raises(Exception, match="No task_id in response"):
                await jaaz_service.create_video_task(prompt="test", model="seedance")


class TestPollForTaskCompletion:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    @pytest.mark.asyncio
    async def test_returns_task_on_success(self, jaaz_service):
        mock_response = make_mock_response(200, json_data={
            'success': True,
            'data': {
                'found': True,
                'task': {'status': 'succeeded', 'result_url': 'http://test.com/result.mp4'}
            }
        })
        mock_session = make_mock_session(get_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            result = await jaaz_service.poll_for_task_completion('task_123', max_attempts=1, interval=0.01)
            assert result['status'] == 'succeeded'

    @pytest.mark.asyncio
    async def test_raises_exception_on_task_failure(self, jaaz_service):
        mock_response = make_mock_response(200, json_data={
            'success': True,
            'data': {
                'found': True,
                'task': {'status': 'failed', 'error': 'Task failed'}
            }
        })
        mock_session = make_mock_session(get_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            with pytest.raises(Exception, match="Task failed"):
                await jaaz_service.poll_for_task_completion('task_123', max_attempts=1, interval=0.01)

    @pytest.mark.asyncio
    async def test_raises_exception_on_task_cancelled(self, jaaz_service):
        mock_response = make_mock_response(200, json_data={
            'success': True,
            'data': {
                'found': True,
                'task': {'status': 'cancelled'}
            }
        })
        mock_session = make_mock_session(get_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            with pytest.raises(Exception, match="Task was cancelled"):
                await jaaz_service.poll_for_task_completion('task_123', max_attempts=1, interval=0.01)


class TestGenerateMagicImage:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    @pytest.mark.asyncio
    async def test_returns_error_when_task_creation_fails(self, jaaz_service):
        with patch.object(jaaz_service, 'create_magic_task', return_value=''):
            result = await jaaz_service.generate_magic_image("data:image/png;base64,abc")
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_returns_error_when_no_result_url(self, jaaz_service):
        with patch.object(jaaz_service, 'create_magic_task', return_value='task_123'), \
             patch.object(jaaz_service, 'poll_for_task_completion', return_value={'result_url': ''}):
            result = await jaaz_service.generate_magic_image("data:image/png;base64,abc")
            assert 'error' in result


class TestGenerateVideoBySeedance:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    @pytest.mark.asyncio
    async def test_raises_exception_on_task_creation_failure(self, jaaz_service):
        mock_response = make_mock_response(400, text_data='Bad Request')
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            with pytest.raises(Exception, match="Failed to create Seedance video task"):
                await jaaz_service.generate_video_by_seedance(prompt="test video", model="seedance")


class TestCreateMidjourneyTask:
    @pytest.fixture
    def jaaz_service(self):
        with patch('web.services.jaaz_service.config_service') as mock_config:
            mock_config.app_config = {'jaaz': {'url': 'https://api.test.com', 'api_key': 'test_key'}}
            from web.services.jaaz_service import JaazService
            return JaazService()

    @pytest.mark.asyncio
    async def test_returns_task_id_on_success(self, jaaz_service):
        mock_response = make_mock_response(200, json_data={'task_id': 'mj_task_456'})
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            result = await jaaz_service.create_midjourney_task(prompt="test image")
            assert result == "mj_task_456"

    @pytest.mark.asyncio
    async def test_raises_exception_on_failure(self, jaaz_service):
        mock_response = make_mock_response(500, text_data='Server Error')
        mock_session = make_mock_session(post_response=mock_response)
        mock_create = make_mock_create_aiohttp(mock_session)

        with patch('web.services.jaaz_service.HttpClient.create_aiohttp', mock_create):
            with pytest.raises(Exception, match="Failed to create Midjourney task"):
                await jaaz_service.create_midjourney_task(prompt="test image")
