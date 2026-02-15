"""
Unit tests for STOMP client.

Tests connection, subscription, message listening, and heartbeat functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.websocket.stomp_client import StompClient, StompError


class TestStompClientInitialization:
    """Test StompClient initialization"""

    def test_stomp_client_can_be_instantiated(self):
        """Test that StompClient can be created"""
        client = StompClient()
        assert client is not None
        assert client.connected is False
        assert client.ws is None
        assert client.session_id is None
        assert client.heartbeat_task is None


class TestStompClientConnection:
    """Test STOMP connection functionality"""

    @pytest.mark.asyncio
    async def test_connect_opens_websocket_with_cookie(self):
        """Test that connect() opens WebSocket with proper headers"""
        client = StompClient()

        with patch('src.websocket.stomp_client.websockets.connect', new_callable=AsyncMock) as mock_connect:
            # Mock WebSocket connection
            mock_ws = AsyncMock()
            # Set recv to return the CONNECTED frame
            async def mock_recv():
                return (
                    "CONNECTED\n"
                    "session:test-session-123\n"
                    "heart-beat:20000,20000\n"
                    "server:RabbitMQ/3.9.10\n"
                    "version:1.2\n"
                    "\n"
                    "\x00"
                )
            mock_ws.recv = mock_recv
            mock_connect.return_value = mock_ws

            await client.connect(
                url="wss://test.com/ws",
                cookie="ASP_NET_SessionId=test123"
            )

            # Verify WebSocket was opened with correct URL and headers
            mock_connect.assert_called_once()
            call_args = mock_connect.call_args
            assert call_args[0][0] == "wss://test.com/ws"
            assert "extra_headers" in call_args[1]
            assert "Cookie" in call_args[1]["extra_headers"]
            assert call_args[1]["extra_headers"]["Cookie"] == "ASP_NET_SessionId=test123"

    @pytest.mark.asyncio
    async def test_connect_sends_stomp_connect_frame(self):
        """Test that connect() sends CONNECT frame with virtual host"""
        client = StompClient()

        with patch('src.websocket.stomp_client.websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            async def mock_recv():
                return (
                    "CONNECTED\n"
                    "session:abc\n"
                    "heart-beat:20000,20000\n"
                    "\n"
                    "\x00"
                )
            mock_ws.recv = mock_recv
            mock_connect.return_value = mock_ws

            await client.connect(
                url="wss://test.com/ws",
                cookie="test_cookie",
                host="WebRT",
                login="rtweb",
                passcode="rtweb"
            )

            # Verify CONNECT frame was sent
            mock_ws.send.assert_called_once()
            sent_frame = mock_ws.send.call_args[0][0]

            assert "CONNECT" in sent_frame
            assert "host:WebRT" in sent_frame
            assert "login:rtweb" in sent_frame
            assert "passcode:rtweb" in sent_frame
            assert "heart-beat:20000,20000" in sent_frame
            assert sent_frame.endswith("\x00")

    @pytest.mark.asyncio
    async def test_connect_receives_and_parses_connected_frame(self):
        """Test that connect() receives CONNECTED and extracts session"""
        client = StompClient()

        with patch('src.websocket.stomp_client.websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            async def mock_recv():
                return (
                    "CONNECTED\n"
                    "session:my-session-456\n"
                    "heart-beat:20000,20000\n"
                    "server:RabbitMQ/3.9.10\n"
                    "\n"
                    "\x00"
                )
            mock_ws.recv = mock_recv
            mock_connect.return_value = mock_ws

            await client.connect(url="wss://test.com", cookie="test")

            # Verify connection state
            assert client.connected is True
            assert client.session_id == "my-session-456"
            assert client.ws is mock_ws

    @pytest.mark.asyncio
    async def test_connect_raises_error_on_stomp_error_frame(self):
        """Test that connect() raises StompError if ERROR received"""
        client = StompClient()

        with patch('src.websocket.stomp_client.websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            async def mock_recv():
                return (
                    "ERROR\n"
                    "message:Authentication failed\n"
                    "\n"
                    "Invalid credentials\x00"
                )
            mock_ws.recv = mock_recv
            mock_ws.close = AsyncMock()
            mock_connect.return_value = mock_ws

            with pytest.raises(ConnectionError) as exc_info:
                await client.connect(url="wss://test.com", cookie="test")

            assert "ERROR" in str(exc_info.value) or "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_starts_heartbeat_task(self):
        """Test that connect() starts background heartbeat task"""
        # Will be implemented in M1.4.9
        pass


class TestStompClientSubscription:
    """Test STOMP subscription functionality"""

    @pytest.mark.asyncio
    async def test_subscribe_raises_if_not_connected(self):
        """Test that subscribe() raises RuntimeError if not connected"""
        client = StompClient()

        # Will fail until M1.4.7 is implemented
        with pytest.raises(NotImplementedError):
            await client.subscribe()

    @pytest.mark.asyncio
    async def test_subscribe_sends_subscribe_frame_to_exchange(self):
        """Test that subscribe() sends SUBSCRIBE to exchange with topics"""
        # Will be implemented in M1.4.7
        pass

    @pytest.mark.asyncio
    async def test_subscribe_uses_default_topics(self):
        """Test that subscribe() uses GAME,TNT,l as default topics"""
        # Will be implemented in M1.4.7
        pass


class TestStompClientListening:
    """Test message listening functionality"""

    @pytest.mark.asyncio
    async def test_listen_raises_if_not_connected(self):
        """Test that listen() raises RuntimeError if not connected"""
        client = StompClient()

        # Will fail until M1.4.8 is implemented
        with pytest.raises(NotImplementedError):
            async for _ in client.listen():
                break

    @pytest.mark.asyncio
    async def test_listen_yields_parsed_json_messages(self):
        """Test that listen() yields parsed JSON from MESSAGE frames"""
        # Will be implemented in M1.4.8
        pass

    @pytest.mark.asyncio
    async def test_listen_filters_heartbeats(self):
        """Test that listen() filters out heartbeat frames"""
        # Will be implemented in M1.4.8
        pass

    @pytest.mark.asyncio
    async def test_listen_raises_on_stomp_error(self):
        """Test that listen() raises StompError on ERROR frame"""
        # Will be implemented in M1.4.8
        pass


class TestStompClientHeartbeat:
    """Test heartbeat functionality"""

    @pytest.mark.asyncio
    async def test_heartbeat_loop_sends_empty_frame_every_20s(self):
        """Test that heartbeat sends \x00 every 20 seconds"""
        # Will be implemented in M1.4.9
        pass

    @pytest.mark.asyncio
    async def test_disconnect_cancels_heartbeat_task(self):
        """Test that disconnect() cancels heartbeat task"""
        # Will be implemented in M1.4.9
        pass


class TestStompClientDisconnect:
    """Test disconnection functionality"""

    @pytest.mark.asyncio
    async def test_disconnect_closes_websocket(self):
        """Test that disconnect() closes WebSocket connection"""
        # Will be implemented in M1.4.9
        pass

    @pytest.mark.asyncio
    async def test_disconnect_sets_connected_to_false(self):
        """Test that disconnect() sets connected flag to False"""
        # Will be implemented in M1.4.9
        pass
