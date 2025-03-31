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
from enum import Enum
from typing import Optional

from stellanow_sdk_python.messages.event import StellaNowEventWrapper


class MessageQueueType(Enum):
    FIFO = "fifo"
    LIFO = "lifo"


class IMessageQueueStrategy(ABC):
    """
    Defines the contract for a message message_queue strategy in StellaNow.
    """

    @abstractmethod
    def enqueue(self, message: StellaNowEventWrapper) -> None:
        """
        Enqueues the specified message into the message_queue.
        :param message: The message in StellaNowMessageWrapper format to be queued.
        """

    @abstractmethod
    def try_dequeue(self) -> Optional[StellaNowEventWrapper]:
        """
        Attempts to dequeue a message from the message_queue.
        :return: The dequeued message if successful; otherwise, None.
        """

    @abstractmethod
    def is_empty(self) -> bool:
        """
        Indicates whether the message_queue is currently empty.
        :return: True if the message_queue is empty; otherwise, False.
        """

    @abstractmethod
    def get_message_count(self) -> int:
        """
        Gets the number of messages currently in the message_queue.
        :return: The count of messages in the message_queue.
        """
