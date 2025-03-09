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
import asyncio
import uuid

from sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy
from sinks.mqtt.stellanow_mqtt_sink import StellaNowMqttSink
from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_messsage_queue_strategy import FifoMessageQueueStrategy

from models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python.sdk import StellaNowSDK
from user_details_message import UserDetailsMessage


async def main():
    queue_strategy = FifoMessageQueueStrategy()
    auth_strategy = OidcMqttAuthStrategy()
    mqtt_sink = StellaNowMqttSink(auth_strategy=auth_strategy)

    sdk = StellaNowSDK(sink=mqtt_sink, queue_strategy=queue_strategy)
    await sdk.start()

    # Create the messages
    message = UserDetailsMessage(
        patronEntityId="12345", user_id="user_67890", phone_number=PhoneNumberModel(country_code=44, number=753594)
    )
    message2 = UserDetailsMessage(
        patronEntityId="12345", user_id="user_98888", phone_number=PhoneNumberModel(country_code=48, number=700000)
    )

    await sdk.send_message(message)
    await sdk.send_message(message2)

    await asyncio.sleep(5)
    await sdk.stop()


if __name__ == "__main__":
    asyncio.run(main())
