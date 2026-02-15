"""
STOMP Client for WebSocket connections.

Handles STOMP 1.2 protocol over WebSocket for RabbitMQ connections.
"""

import asyncio
import json
from typing import Optional, List, AsyncIterator, Dict, Any
import websockets

from src.websocket.stomp_frames import (
    encode_connect_frame,
    encode_subscribe_frame,
    encode_heartbeat,
    parse_stomp_frame
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class StompError(Exception):
    """Raised when STOMP protocol error occurs"""
    pass


class StompClient:
    """
    STOMP 1.2 client for WebSocket connections.

    Handles connection, subscription, message listening, and heartbeats
    for STOMP protocol over WebSocket (RabbitMQ).

    Attributes:
        ws: WebSocket connection
        connected: Connection state
        session_id: STOMP session ID from server
        heartbeat_task: Background task for sending heartbeats
    """

    def __init__(self):
        """Initialize STOMP client."""
        self.ws: Optional[Any] = None  # WebSocket connection
        self.connected: bool = False
        self.session_id: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        logger.debug("StompClient initialized")

    async def connect(
        self,
        url: str,
        cookie: str,
        host: str = "WebRT",
        login: str = "rtweb",
        passcode: str = "rtweb",
        heartbeat: int = 20000
    ) -> None:
        """
        Connect to WebSocket and perform STOMP handshake.

        Args:
            url: WebSocket URL (e.g., wss://be.bookmaker.eu/...)
            cookie: Session cookie (e.g., ASP_NET_SessionId=...)
            host: STOMP virtual host (default: WebRT)
            login: STOMP username (default: rtweb)
            passcode: STOMP password (default: rtweb)
            heartbeat: Heartbeat interval in milliseconds (default: 20000)

        Raises:
            ConnectionError: If connection or STOMP handshake fails
            StompError: If STOMP ERROR frame received
        """
        raise NotImplementedError("To be implemented in M1.4.6")

    async def subscribe(
        self,
        exchange: str = "BetSlipRTv4Topics",
        topics: Optional[List[str]] = None,
        sub_id: str = "sub-0"
    ) -> None:
        """
        Subscribe to RabbitMQ exchange with routing keys.

        Args:
            exchange: Exchange name (default: BetSlipRTv4Topics)
            topics: Routing keys (default: ["GAME", "TNT", "l"])
            sub_id: Subscription ID (default: sub-0)

        Raises:
            RuntimeError: If not connected
            StompError: If STOMP ERROR frame received
        """
        raise NotImplementedError("To be implemented in M1.4.7")

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for MESSAGE frames and yield parsed JSON data.

        Filters out heartbeats and yields only data messages.

        Yields:
            Parsed JSON message data

        Raises:
            RuntimeError: If not connected
            StompError: If STOMP ERROR frame received
            websockets.ConnectionClosed: If WebSocket disconnects
        """
        raise NotImplementedError("To be implemented in M1.4.8")
        # Make this a generator to satisfy type hints
        if False:  # pragma: no cover
            yield {}

    async def disconnect(self) -> None:
        """
        Disconnect from WebSocket and cleanup resources.

        Cancels heartbeat task and closes WebSocket connection.
        """
        raise NotImplementedError("To be implemented in M1.4.9")

    async def _heartbeat_loop(self) -> None:
        """
        Background task to send heartbeats every 20 seconds.

        Sends empty frame (\x00) to keep connection alive.
        """
        raise NotImplementedError("To be implemented in M1.4.9")
