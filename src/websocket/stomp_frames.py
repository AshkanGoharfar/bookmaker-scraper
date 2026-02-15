"""
STOMP 1.2 Frame Encoder/Decoder

Simple implementation for STOMP protocol over WebSocket.
Handles CONNECT, SUBSCRIBE, MESSAGE, and HEARTBEAT frames.
"""

from typing import Dict, List, Any


def encode_connect_frame(
    host: str,
    login: str,
    passcode: str,
    heartbeat: int = 20000
) -> str:
    """
    Encode STOMP CONNECT frame.

    Args:
        host: Virtual host (e.g., "WebRT")
        login: Username (e.g., "rtweb")
        passcode: Password (e.g., "rtweb")
        heartbeat: Heartbeat interval in milliseconds

    Returns:
        STOMP CONNECT frame as string with NULL terminator
    """
    return (
        "CONNECT\n"
        "accept-version:1.2\n"
        f"host:{host}\n"
        f"login:{login}\n"
        f"passcode:{passcode}\n"
        f"heart-beat:{heartbeat},{heartbeat}\n"
        "\n"
        "\x00"
    )


def encode_subscribe_frame(
    exchange: str,
    topics: List[str],
    sub_id: str = "sub-0",
    use_wildcard: bool = False
) -> str:
    """
    Encode STOMP SUBSCRIBE frame for RabbitMQ exchange.

    Args:
        exchange: Exchange name (e.g., "BetSlipRTv4Topics")
        topics: Routing keys (e.g., ["GAME", "TNT", "l"])
        sub_id: Subscription ID
        use_wildcard: If True, use '#' wildcard to receive ALL messages

    Returns:
        STOMP SUBSCRIBE frame as string with NULL terminator
    """
    # Use wildcard to get ALL messages, or specific routing keys
    if use_wildcard:
        routing_keys = "#"  # RabbitMQ wildcard: matches any routing key
    else:
        routing_keys = ".".join(topics)

    return (
        "SUBSCRIBE\n"
        f"id:{sub_id}\n"
        f"destination:/exchange/{exchange}/{routing_keys}\n"
        "ack:auto\n"
        "\n"
        "\x00"
    )


def parse_stomp_frame(data: str) -> Dict[str, Any]:
    """
    Parse STOMP frame into dictionary.

    Args:
        data: Raw STOMP frame string

    Returns:
        Dictionary with 'command', 'headers', 'body', 'is_heartbeat'
    """
    # Heartbeat detection (empty frame or just NULL)
    if not data or data == "\x00" or len(data) == 1:
        return {
            "command": "HEARTBEAT",
            "headers": {},
            "body": "",
            "is_heartbeat": True
        }

    # Remove NULL terminator
    data = data.rstrip("\x00")

    # Split into header section and body
    parts = data.split("\n\n", 1)
    header_section = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    # Parse command and headers
    lines = header_section.split("\n")
    command = lines[0] if lines else ""

    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key] = value

    return {
        "command": command,
        "headers": headers,
        "body": body,
        "is_heartbeat": False
    }


def encode_heartbeat() -> str:
    """
    Encode STOMP heartbeat (empty frame).

    Returns:
        NULL byte
    """
    return "\x00"
