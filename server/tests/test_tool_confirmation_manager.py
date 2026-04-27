import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta


class TestToolConfirmationManagerImports:
    """Test tool_confirmation_manager imports"""

    def test_tool_confirmation_manager_exists(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        assert ToolConfirmationManager is not None

    def test_tool_confirmation_request_exists(self):
        from agents.tool_confirmation_manager import ToolConfirmationRequest
        assert ToolConfirmationRequest is not None

    def test_global_instance_exists(self):
        from agents.tool_confirmation_manager import tool_confirmation_manager
        assert tool_confirmation_manager is not None


class TestToolConfirmationRequest:
    """Test ToolConfirmationRequest dataclass"""

    def test_creation_with_required_fields(self):
        from agents.tool_confirmation_manager import ToolConfirmationRequest
        request = ToolConfirmationRequest(
            tool_call_id='call_123',
            session_id='session_456',
            tool_name='generate_image',
            arguments={'prompt': 'a cat'},
            created_at=datetime.now()
        )
        assert request.tool_call_id == 'call_123'
        assert request.session_id == 'session_456'
        assert request.tool_name == 'generate_image'
        assert request.confirmed is None

    def test_creation_with_optional_confirmed(self):
        from agents.tool_confirmation_manager import ToolConfirmationRequest
        request = ToolConfirmationRequest(
            tool_call_id='call_123',
            session_id='session_456',
            tool_name='generate_image',
            arguments={'prompt': 'a cat'},
            created_at=datetime.now(),
            confirmed=True
        )
        assert request.confirmed is True


class TestToolConfirmationManagerInit:
    """Test ToolConfirmationManager initialization"""

    def test_initializes_with_empty_pending(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        manager = ToolConfirmationManager()
        assert manager.pending_confirmations == {}
        assert manager.confirmation_timeout == timedelta(minutes=5)


class TestRequestConfirmation:
    """Test ToolConfirmationManager.request_confirmation method"""

    @pytest.fixture
    def manager(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        return ToolConfirmationManager()

    @pytest.mark.asyncio
    async def test_adds_pending_confirmation(self, manager):
        with patch.object(manager, '_wait_for_confirmation', new_callable=AsyncMock):
            result = await manager.request_confirmation(
                tool_call_id='call_1',
                session_id='session_1',
                tool_name='test_tool',
                arguments={}
            )
            assert 'call_1' in manager.pending_confirmations

    @pytest.mark.asyncio
    async def test_returns_true_when_confirmed(self, manager):
        async def mock_wait(tool_call_id: str):
            manager.pending_confirmations['call_1'].confirmed = True

        with patch.object(manager, '_wait_for_confirmation', mock_wait):
            manager.pending_confirmations['call_1'] = type('obj', (object,), {
                'confirmed': True,
                'tool_call_id': 'call_1',
                'session_id': 'session_1',
                'tool_name': 'test',
                'arguments': {},
                'created_at': datetime.now()
            })()

            result = await manager.request_confirmation(
                tool_call_id='call_1',
                session_id='session_1',
                tool_name='test_tool',
                arguments={}
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_timeout(self, manager):
        with patch.object(manager, '_wait_for_confirmation', new_callable=AsyncMock):
            await manager.request_confirmation(
                tool_call_id='call_1',
                session_id='session_1',
                tool_name='test_tool',
                arguments={}
            )
            assert 'call_1' in manager.pending_confirmations


class TestConfirmTool:
    """Test ToolConfirmationManager.confirm_tool method"""

    @pytest.fixture
    def manager(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        return ToolConfirmationManager()

    def test_returns_true_when_request_exists(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest
        manager.pending_confirmations['call_1'] = ToolConfirmationRequest(
            tool_call_id='call_1',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now()
        )

        result = manager.confirm_tool('call_1')
        assert result is True
        assert manager.pending_confirmations['call_1'].confirmed is True

    def test_returns_false_when_request_not_found(self, manager):
        result = manager.confirm_tool('nonexistent_call')
        assert result is False


class TestCancelConfirmation:
    """Test ToolConfirmationManager.cancel_confirmation method"""

    @pytest.fixture
    def manager(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        return ToolConfirmationManager()

    def test_returns_true_when_request_exists(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest
        manager.pending_confirmations['call_1'] = ToolConfirmationRequest(
            tool_call_id='call_1',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now()
        )

        result = manager.cancel_confirmation('call_1')
        assert result is True
        assert manager.pending_confirmations['call_1'].confirmed is False

    def test_returns_false_when_request_not_found(self, manager):
        result = manager.cancel_confirmation('nonexistent_call')
        assert result is False


class TestGetPendingRequest:
    """Test ToolConfirmationManager.get_pending_request method"""

    @pytest.fixture
    def manager(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        return ToolConfirmationManager()

    def test_returns_request_when_exists(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest
        request = ToolConfirmationRequest(
            tool_call_id='call_1',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now()
        )
        manager.pending_confirmations['call_1'] = request

        result = manager.get_pending_request('call_1')
        assert result is request

    def test_returns_none_when_not_found(self, manager):
        result = manager.get_pending_request('nonexistent_call')
        assert result is None


class TestCleanupExpired:
    """Test ToolConfirmationManager.cleanup_expired method"""

    @pytest.fixture
    def manager(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        return ToolConfirmationManager()

    def test_removes_expired_requests(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest

        # Add an expired request
        manager.pending_confirmations['expired_call'] = ToolConfirmationRequest(
            tool_call_id='expired_call',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now() - timedelta(minutes=10)  # 10 minutes ago
        )

        # Add a valid request
        manager.pending_confirmations['valid_call'] = ToolConfirmationRequest(
            tool_call_id='valid_call',
            session_id='session_2',
            tool_name='test',
            arguments={},
            created_at=datetime.now()  # just now
        )

        manager.cleanup_expired()

        assert 'expired_call' not in manager.pending_confirmations
        assert 'valid_call' in manager.pending_confirmations

    def test_does_nothing_when_all_valid(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest

        manager.pending_confirmations['call_1'] = ToolConfirmationRequest(
            tool_call_id='call_1',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now()
        )

        manager.cleanup_expired()

        assert len(manager.pending_confirmations) == 1


class TestWaitForConfirmation:
    """Test ToolConfirmationManager._wait_for_confirmation method"""

    @pytest.fixture
    def manager(self):
        from agents.tool_confirmation_manager import ToolConfirmationManager
        return ToolConfirmationManager()

    @pytest.mark.asyncio
    async def test_returns_when_confirmed(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest

        manager.pending_confirmations['call_1'] = ToolConfirmationRequest(
            tool_call_id='call_1',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now(),
            confirmed=True
        )

        # Should return immediately since confirmed is already True
        await manager._wait_for_confirmation('call_1')

    @pytest.mark.asyncio
    async def test_continues_until_confirmed(self, manager):
        from agents.tool_confirmation_manager import ToolConfirmationRequest

        manager.pending_confirmations['call_1'] = ToolConfirmationRequest(
            tool_call_id='call_1',
            session_id='session_1',
            tool_name='test',
            arguments={},
            created_at=datetime.now(),
            confirmed=None
        )

        # Set confirmed after a short delay
        async def set_confirmed():
            await asyncio.sleep(0.05)
            manager.pending_confirmations['call_1'].confirmed = True

        import asyncio
        asyncio.create_task(set_confirmed())

        await manager._wait_for_confirmation('call_1')
        assert manager.pending_confirmations['call_1'].confirmed is True
