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
        # Not connected, should raise
        with pytest.raises(RuntimeError) as exc_info:
            await client.subscribe()
        assert "not connected" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_subscribe_sends_subscribe_frame_to_exchange(self):
        """Test that subscribe() sends SUBSCRIBE to exchange with topics"""
        client = StompClient()
        client.ws = AsyncMock()
        client.connected = True

        await client.subscribe(
            exchange="BetSlipRTv4Topics",
            topics=["GAME", "TNT", "l"]
        )

        # Verify SUBSCRIBE frame was sent
        client.ws.send.assert_called_once()
        sent_frame = client.ws.send.call_args[0][0]

        assert "SUBSCRIBE" in sent_frame
        assert "destination:/exchange/BetSlipRTv4Topics/GAME.TNT.l" in sent_frame
        assert "id:sub-0" in sent_frame
        assert "ack:auto" in sent_frame
        assert sent_frame.endswith("\x00")

    @pytest.mark.asyncio
    async def test_subscribe_uses_default_topics(self):
        """Test that subscribe() uses GAME,TNT,l as default topics"""
        client = StompClient()
        client.ws = AsyncMock()
        client.connected = True

        # Call without specifying topics (should use defaults)
        await client.subscribe()

        # Verify default topics used
        client.ws.send.assert_called_once()
        sent_frame = client.ws.send.call_args[0][0]

        # Should contain default topics: GAME, TNT, l
        assert "GAME" in sent_frame
        assert "TNT" in sent_frame
        assert ".l" in sent_frame or "l\n" in sent_frame


class TestStompClientListening:
    """Test message listening functionality"""

    @pytest.mark.asyncio
    async def test_listen_raises_if_not_connected(self):
        """Test that listen() raises RuntimeError if not connected"""
        client = StompClient()
        # Not connected, should raise
        with pytest.raises(RuntimeError) as exc_info:
            async for _ in client.listen():
                break
        assert "not connected" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_listen_yields_parsed_json_messages(self):
        """Test that listen() yields parsed JSON from MESSAGE frames"""
        client = StompClient()
        client.ws = AsyncMock()
        client.connected = True

        # Mock WebSocket to return 3 MESSAGE frames then close
        messages = [
            # MESSAGE 1: Game odds update
            (
                "MESSAGE\n"
                "destination:/exchange/BetSlipRTv4Topics\n"
                "message-id:123\n"
                "subscription:sub-0\n"
                "content-type:application/json\n"
                "\n"
                '{"type":"GAME","gameId":12345,"odds":2.5}\x00'
            ),
            # MESSAGE 2: Live update
            (
                "MESSAGE\n"
                "destination:/exchange/BetSlipRTv4Topics\n"
                "message-id:124\n"
                "subscription:sub-0\n"
                "\n"
                '{"type":"l","eventId":67890,"score":"2-1"}\x00'
            ),
        ]

        call_count = 0
        async def mock_recv():
            nonlocal call_count
            if call_count < len(messages):
                msg = messages[call_count]
                call_count += 1
                return msg
            else:
                # Simulate WebSocket close
                from websockets.exceptions import ConnectionClosed
                raise ConnectionClosed(None, None)

        client.ws.recv = mock_recv

        # Collect yielded messages
        received = []
        try:
            async for message in client.listen():
                received.append(message)
        except Exception:
            pass  # Expected ConnectionClosed

        # Verify we got both JSON messages parsed
        assert len(received) == 2
        assert received[0]["type"] == "GAME"
        assert received[0]["gameId"] == 12345
        assert received[0]["odds"] == 2.5
        assert received[1]["type"] == "l"
        assert received[1]["eventId"] == 67890

    @pytest.mark.asyncio
    async def test_listen_filters_heartbeats(self):
        """Test that listen() filters out heartbeat frames"""
        client = StompClient()
        client.ws = AsyncMock()
        client.connected = True

        # Mix heartbeats with real messages
        frames = [
            "\x00",  # Heartbeat
            (
                "MESSAGE\n"
                "message-id:1\n"
                "\n"
                '{"type":"GAME","id":1}\x00'
            ),
            "\x00",  # Heartbeat
            "\x00",  # Heartbeat
            (
                "MESSAGE\n"
                "message-id:2\n"
                "\n"
                '{"type":"TNT","id":2}\x00'
            ),
        ]

        call_count = 0
        async def mock_recv():
            nonlocal call_count
            if call_count < len(frames):
                frame = frames[call_count]
                call_count += 1
                return frame
            else:
                from websockets.exceptions import ConnectionClosed
                raise ConnectionClosed(None, None)

        client.ws.recv = mock_recv

        # Collect yielded messages
        received = []
        try:
            async for message in client.listen():
                received.append(message)
        except Exception:
            pass

        # Should only get 2 messages, heartbeats filtered out
        assert len(received) == 2
        assert received[0]["id"] == 1
        assert received[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_listen_raises_on_stomp_error(self):
        """Test that listen() raises StompError on ERROR frame"""
        client = StompClient()
        client.ws = AsyncMock()
        client.connected = True

        # Mock WebSocket to return ERROR frame
        async def mock_recv():
            return (
                "ERROR\n"
                "message:Subscription error\n"
                "\n"
                "Invalid subscription\x00"
            )

        client.ws.recv = mock_recv

        # Should raise StompError
        with pytest.raises(StompError) as exc_info:
            async for _ in client.listen():
                pass

        assert "Subscription error" in str(exc_info.value) or "ERROR" in str(exc_info.value)


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
