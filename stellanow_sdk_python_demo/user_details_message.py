"""
This file is auto-generated by StellaNowCLI. DO NOT EDIT.

Event ID: d3fee488-812f-4bd5-bf06-b40ef8befb30
Generated: 2025-02-26T09:24:37Z
"""

from typing import Dict

from models.phone_number_model import PhoneNumberModel

from stellanow_sdk_python.messages.message import EntityType, StellaNowMessageBase


class UserDetailsMessage(StellaNowMessageBase):
    patron: str
    phone_number: PhoneNumberModel
    user_id: str

    def __init__(self, patron: str, phone_number: PhoneNumberModel, user_id: str):
        super().__init__(
            event_name="user_details",
            entities=[EntityType(entityTypeDefinitionId="patron", entityId=patron)],
            patron=patron,
            phone_number=phone_number,
            user_id=user_id,
        )

    def to_json(self) -> Dict:
        """Serialize the message fields to a dictionary, excluding entity-related fields."""
        return {"phone_number": self.phone_number.model_dump(), "user_id": self.user_id}


"""
Generated from:

{
    "createdAt": "2025-02-25 14:25:55",
    "updatedAt": "2025-02-26 09:24:32",
    "id": "d3fee488-812f-4bd5-bf06-b40ef8befb30",
    "name": "user_details",
    "projectId": "52b212f7-3da9-47eb-a2a8-adc9248dba74",
    "isActive": true,
    "description": "",
    "fields": [
        {
            "id": "9ff36bff-aa91-4207-b7b8-4827667b2782",
            "name": "user_id",
            "fieldType": {
                "value": "String"
            },
            "required": true,
            "subfields": []
        },
        {
            "id": "5d7a9b73-aca3-4685-b4b7-30c485e4d92c",
            "name": "phone_number",
            "fieldType": {
                "value": "Model",
                "modelRef": "0bb918a9-d5d5-4210-a93e-8683f25f0f28"
            },
            "required": false,
            "subfields": [
                {
                    "id": "bedff932-a466-451a-9874-9b1401b42f68",
                    "name": "country_code",
                    "fieldType": {
                        "value": "Integer"
                    },
                    "required": true,
                    "path": [
                        "phone_number",
                        "country_code"
                    ],
                    "modelFieldId": "3c14a95d-6f21-44c5-accf-914d72c1e01d"
                },
                {
                    "id": "2985a146-b5bc-4c2a-a414-689a07c74445",
                    "name": "number",
                    "fieldType": {
                        "value": "Integer"
                    },
                    "required": true,
                    "path": [
                        "phone_number",
                        "number"
                    ],
                    "modelFieldId": "05746ab2-84ea-4b77-adbb-8d91c22d050b"
                }
            ]
        }
    ],
    "entities": [
        {
            "id": "2ad73e39-f4bf-471e-b44e-b0f7b50f0096",
            "name": "patron"
        }
    ]
}
"""
