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
        logger.info(f"Connecting to {url}...")

        # Open WebSocket connection with cookie and required headers
        headers = {
            "Cookie": cookie,
            "Origin": "https://www.bookmaker.eu",  # Required by server
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            self.ws = await websockets.connect(url, additional_headers=headers)
            logger.debug("WebSocket connection established")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket: {e}") from e

        # Send STOMP CONNECT frame
        connect_frame = encode_connect_frame(
            host=host,
            login=login,
            passcode=passcode,
            heartbeat=heartbeat
        )
        await self.ws.send(connect_frame)
        logger.debug("CONNECT frame sent")

        # Wait for CONNECTED response
        try:
            response = await self.ws.recv()
            frame = parse_stomp_frame(response)

            if frame["command"] == "ERROR":
                error_msg = frame["headers"].get("message", "Unknown error")
                raise ConnectionError(f"STOMP ERROR: {error_msg}")

            if frame["command"] != "CONNECTED":
                raise ConnectionError(
                    f"Expected CONNECTED frame, got {frame['command']}"
                )

            # Extract session ID
            self.session_id = frame["headers"].get("session")
            self.connected = True

            logger.info(f"STOMP connected successfully. Session: {self.session_id}")

            # Start heartbeat background task
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.debug("Heartbeat task started")

        except Exception as e:
            # Close WebSocket on error
            if self.ws:
                await self.ws.close()
            self.ws = None
            self.connected = False
            raise

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
        if not self.connected or not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")

        # Use default topics if not specified
        if topics is None:
            topics = ["GAME", "TNT", "l"]

        logger.info(f"Subscribing to exchange {exchange} with topics: {topics}")

        # Send STOMP SUBSCRIBE frame
        subscribe_frame = encode_subscribe_frame(
            exchange=exchange,
            topics=topics,
            sub_id=sub_id
        )
        await self.ws.send(subscribe_frame)

        logger.info(f"Subscribed to {exchange} (topics: {', '.join(topics)})")

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
        if not self.connected or not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.debug("Starting to listen for messages...")

        while True:
            try:
                # Receive raw frame from WebSocket
                raw_frame = await self.ws.recv()

                # Parse STOMP frame
                frame = parse_stomp_frame(raw_frame)

                # Skip heartbeats
                if frame["is_heartbeat"]:
                    logger.debug("Received heartbeat")
                    continue

                # Handle ERROR frames
                if frame["command"] == "ERROR":
                    error_msg = frame["headers"].get("message", "Unknown error")
                    logger.error(f"STOMP ERROR received: {error_msg}")
                    raise StompError(f"STOMP ERROR: {error_msg}")

                # Handle MESSAGE frames
                if frame["command"] == "MESSAGE":
                    body = frame["body"]
                    if body:
                        try:
                            # Parse JSON body and yield
                            message_data = json.loads(body)
                            logger.debug(f"Received message: {message_data}")
                            yield message_data
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON message: {e}")
                            continue
                    else:
                        logger.debug("Received MESSAGE with empty body")
                        continue

            except Exception as e:
                # Re-raise if it's our StompError
                if isinstance(e, StompError):
                    raise
                # Otherwise log and re-raise (likely ConnectionClosed)
                logger.error(f"Error in listen loop: {e}")
                raise

    async def disconnect(self) -> None:
        """
        Disconnect from WebSocket and cleanup resources.

        Cancels heartbeat task and closes WebSocket connection.
        """
        logger.info("Disconnecting...")

        # Cancel heartbeat task if running
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                logger.debug("Heartbeat task cancelled")

        # Close WebSocket connection
        if self.ws:
            await self.ws.close()
            logger.debug("WebSocket closed")

        # Reset connection state
        self.connected = False
        self.session_id = None
        self.ws = None
        self.heartbeat_task = None

        logger.info("Disconnected successfully")

    async def _heartbeat_loop(self) -> None:
        """
        Background task to send heartbeats every 20 seconds.

        Sends empty frame (\x00) to keep connection alive.
        """
        logger.debug("Heartbeat loop started")

        try:
            while True:
                # Wait 20 seconds
                await asyncio.sleep(20)

                # Send heartbeat
                if self.ws and self.connected:
                    heartbeat = encode_heartbeat()
                    await self.ws.send(heartbeat)
                    logger.debug("Heartbeat sent")
                else:
                    logger.warning("Cannot send heartbeat - not connected")
                    break

        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")
            raise
