
"""
 This file is auto-generated by StellaNowCLI. DO NOT EDIT.

 ID: ccf14a97-110c-4b0d-977c-f96c04868367
 Generated: 2025-03-30T14:34:24Z
"""

from pydantic import Field

from stellanow_sdk_python.messages.message import Entity, StellaNowMessageBase

class StoreReceiptMessage(StellaNowMessageBase):
    transaction_id: str = Field(None, serialization_alias='transaction_id')

    def __init__(self, patron: str, local_shop: str, transaction_id: str):
        super().__init__(
            event_name="store_receipt",
            entities=[
                Entity(entity_type_definition_id="patron", entity_id=patron),
                Entity(entity_type_definition_id="local_shop", entity_id=local_shop)
            ],
            patron=patron,
            local_shop=local_shop,
            transaction_id=transaction_id
        )


"""
 Generated from:
{
    "createdAt": "2025-03-30 13:11:51",
    "updatedAt": "2025-03-30 13:11:54",
    "id": "ccf14a97-110c-4b0d-977c-f96c04868367",
    "name": "store_receipt",
    "projectId": "3af7b6f4-8afa-46ce-8df2-c9d86e8be3e9",
    "isActive": true,
    "description": "",
    "fields": [
        {
            "id": "36fa7066-9514-4258-9a25-de761723981e",
            "name": "transaction_id",
            "fieldType": {
                "value": "String"
            },
            "required": false,
            "subfields": []
        }
    ],
    "entities": [
        {
            "id": "194964c4-1caa-4347-9e91-5c275f9ba474",
            "name": "patron"
        },
        {
            "id": "2d524c5d-229f-4f5d-a84a-1bcd52ca622a",
            "name": "local_shop"
        }
    ]
}
"""