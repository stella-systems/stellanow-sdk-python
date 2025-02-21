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
import json
import uuid
from datetime import datetime

from stellanow_sdk_python.messages.message_base import StellaNowMessageBase


class StellaNowMessageWrapper:
    def __init__(self, message: StellaNowMessageBase, organization_id: str, project_id: str, event_id: str):
        self.key = {"organizationId": organization_id, "projectId": project_id, "eventId": event_id}
        self.value = {
            "metadata": {
                "messageId": str(uuid.uuid4()),
                "messageOriginDateUTC": datetime.utcnow().isoformat() + "Z",
                "eventTypeDefinitionId": message.event_name,
                "entityTypeIds": [
                    {"entityTypeDefinitionId": entity["type"], "entityId": entity["id"]} for entity in message.entities
                ],
            },
            "payload": json.dumps(message.to_dict()),
        }

    def to_json(self):
        """
        Serialize the wrapper to a JSON-formatted string.
        """
        return json.dumps({"key": self.key, "value": self.value}, indent=2)
