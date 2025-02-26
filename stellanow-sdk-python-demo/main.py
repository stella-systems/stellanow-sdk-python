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

from stellanow_sdk_python.settings import ORGANIZATION_ID, PROJECT_ID

from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper
from models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python.sdk import StellaNowSDK
from user_details_message import UserDetailsMessage


async def main():
    sdk = StellaNowSDK()
    await sdk.start()

    # Create the message
    message = UserDetailsMessage(
        patronEntityId="12345", user_id="user_67890", phone_number=PhoneNumberModel(country_code=44, number=753594)
    )

    # Wrap the message
    wrapped_message = StellaNowMessageWrapper.create(
        message=message,
        organization_id=ORGANIZATION_ID,
        project_id=PROJECT_ID,
        event_id=str(uuid.uuid4()),
    )

    # Send the wrapped message
    await sdk.send_message(wrapped_message.model_dump_json())

    await asyncio.sleep(5)
    sdk.stop()


if __name__ == "__main__":
    asyncio.run(main())
