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

from abc import ABC, abstractmethod

from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper


class IStellaNowSink(ABC):
    """
    Defines the contract for a Sink in StellaNow.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Connects to the sink (e.g., MQTT broker, Kafka).
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnects from the sink.
        """

    @abstractmethod
    async def send_message(self, message: StellaNowMessageWrapper) -> None:
        """
        Sends a message to the sink.
        :param message: The message to send.
        """

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Checks if the sink is connected.
        :return: True if connected; otherwise, False.
        """
