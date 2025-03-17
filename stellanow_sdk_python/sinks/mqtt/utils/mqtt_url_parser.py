"""
Copyright (C) 2022-2025 Stella Technologies (UK) Limited.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from typing import Literal
from urllib.parse import urlparse


class MqttUrlConfig:
    def __init__(
        self, scheme: str, hostname: str, port: int, transport: Literal["tcp", "websockets", "unix"], use_tls: bool
    ):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.transport = transport
        self.use_tls = use_tls


def parse_mqtt_url(url: str) -> MqttUrlConfig:
    """
    Parse an MQTT URL and return its configuration components.

    Args:
        url (str): The MQTT URL, e.g., 'mqtt-tcp://ingestor.dev.stella.cloud:1883',
                  'mqtts://broker:8883', 'ws://broker:80', or 'wss://broker:443'

    Returns:
        MqttUrlConfig: Object containing scheme, hostname, port, transport, and TLS flag.

    Raises:
        ValueError: If the URL is malformed or unsupported.
    """
    parsed = urlparse(url)

    # Validate scheme and determine transport/TLS
    scheme = parsed.scheme.lower()
    transport: Literal["tcp", "websockets"]
    use_tls: bool

    match scheme:
        case "mqtt" | "mqtt-tcp":
            transport = "tcp"
            use_tls = False
        case "mqtts":
            transport = "tcp"
            use_tls = True
        case "ws":
            transport = "websockets"
            use_tls = False
        case "wss":
            transport = "websockets"
            use_tls = True
        case _:
            raise ValueError(f"Unsupported MQTT scheme: {scheme}. Use 'mqtt', 'mqtt-tcp', 'mqtts', 'ws', or 'wss'.")

    # Extract hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("No hostname provided in MQTT URL.")

    # Extract port (default based on scheme if not provided)
    port = parsed.port
    if port is None:
        match scheme:
            case "mqtts":
                port = 8883
            case "wss":
                port = 443
            case "ws":
                port = 80
            case "mqtt" | "mqtt-tcp":
                port = 1883
            case _:
                raise ValueError(f"No default port defined for scheme: {scheme}")

    return MqttUrlConfig(scheme=scheme, hostname=hostname, port=port, transport=transport, use_tls=use_tls)
