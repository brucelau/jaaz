import pytest
from unittest.mock import patch, MagicMock


class TestWebsocketsManager:
    def test_add_connection(self):
        from ws_manager.manager import add_connection, active_connections
        add_connection('test_sid', {'user': 'test'})
        assert 'test_sid' in active_connections
        assert active_connections['test_sid'] == {'user': 'test'}

    def test_remove_connection(self):
        from ws_manager.manager import add_connection, remove_connection, active_connections
        add_connection('test_sid', {'user': 'test'})
        remove_connection('test_sid')
        assert 'test_sid' not in active_connections

    def test_get_all_socket_ids(self):
        from ws_manager.manager import add_connection, get_all_socket_ids
        add_connection('sid1', {'user': 'user1'})
        add_connection('sid2', {'user': 'user2'})
        sids = get_all_socket_ids()
        assert 'sid1' in sids
        assert 'sid2' in sids

    def test_get_connection_count(self):
        from ws_manager.manager import add_connection, remove_connection, get_connection_count
        add_connection('sid1', {})
        add_connection('sid2', {})
        assert get_connection_count() == 2
        remove_connection('sid1')
        assert get_connection_count() == 1

    def test_remove_nonexistent_connection(self):
        from ws_manager.manager import remove_connection
        remove_connection('nonexistent')


class TestWebsocketsEmitter:
    def test_broadcast_session_update_function_exists(self):
        from ws_manager.emitter import broadcast_session_update
        assert callable(broadcast_session_update)

    def test_send_to_websocket_function_exists(self):
        from ws_manager.emitter import send_to_websocket
        assert callable(send_to_websocket)

    def test_broadcast_init_done_function_exists(self):
        from ws_manager.emitter import broadcast_init_done
        assert callable(broadcast_init_done)


class TestWebsocketsHandlers:
    def test_connect_handler_exists(self):
        from ws_manager.handlers import connect
        assert callable(connect)

    def test_disconnect_handler_exists(self):
        from ws_manager.handlers import disconnect
        assert callable(disconnect)

    def test_ping_handler_exists(self):
        from ws_manager.handlers import ping
        assert callable(ping)


class TestWebsocketsPackage:
    def test_sio_exported(self):
        from ws_manager import sio
        assert sio is not None

    def test_all_exports_available(self):
        from ws_manager import (
            sio,
            add_connection,
            remove_connection,
            get_all_socket_ids,
            get_connection_count,
            broadcast_session_update,
            send_to_websocket,
            broadcast_init_done,
            connect,
            disconnect,
            ping,
        )
        assert callable(broadcast_session_update)
        assert callable(send_to_websocket)
        assert callable(broadcast_init_done)
        assert callable(connect)
        assert callable(disconnect)
        assert callable(ping)
