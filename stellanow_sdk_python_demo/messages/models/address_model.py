
"""
 This file is auto-generated by StellaNowCLI. DO NOT EDIT.

 ID: 8faf7ffa-8d84-4704-b50c-9b75606e609a
 Generated: 2025-03-30T14:34:24Z
"""

from pydantic import Field
from stellanow_sdk_python.messages.message import StellaNowMessageBase


class AddressModel(StellaNowMessageBase):
    city: str = Field(None, serialization_alias='city')
    country: str = Field(None, serialization_alias='country')
    county: str = Field(None, serialization_alias='county')
    first_line: str = Field(None, serialization_alias='first_line')
    post_code: str = Field(None, serialization_alias='post_code')
    second_line: str = Field(None, serialization_alias='second_line')


"""
 Generated from:
{
    "createdAt": "2025-03-30 13:55:59",
    "updatedAt": "2025-03-30 13:55:59",
    "id": "8faf7ffa-8d84-4704-b50c-9b75606e609a",
    "name": "address",
    "description": "",
    "fields": [
        {
            "id": "aff56841-c0d6-4b65-b277-413091724d07",
            "name": "city",
            "fieldType": {
                "value": "String"
            }
        },
        {
            "id": "9f48e2df-79c3-4d61-b1ac-bef22d4c60d0",
            "name": "country",
            "fieldType": {
                "value": "String"
            }
        },
        {
            "id": "55ca7d08-fe78-4ebf-9092-123576c70ac1",
            "name": "county",
            "fieldType": {
                "value": "String"
            }
        },
        {
            "id": "033b2474-2c5f-4ae2-bc91-5290ed3b1c5b",
            "name": "first_line",
            "fieldType": {
                "value": "String"
            }
        },
        {
            "id": "c44df296-e14e-4801-85d5-060a3dabc0a7",
            "name": "post_code",
            "fieldType": {
                "value": "String"
            }
        },
        {
            "id": "8af2b111-633b-4e4b-8f9f-a1d8c34c7261",
            "name": "second_line",
            "fieldType": {
                "value": "String"
            }
        }
    ]
}
"""