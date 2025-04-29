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

from typing import Optional
from uuid import UUID

from pydantic import Field, field_serializer

from stellanow_sdk_python.messages.base import StellaNowBaseModel
from stellanow_sdk_python.messages.message import Entity, StellaNowMessageWrapper


class EventKey(StellaNowBaseModel):
    organization_id: UUID = Field(..., serialization_alias="organizationId")
    project_id: UUID = Field(..., serialization_alias="projectId")
    entity_id: str = Field(..., serialization_alias="entityId")
    entity_type_definition_id: str = Field(..., serialization_alias="entityTypeDefinitionId")

    @field_serializer("organization_id", "project_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class StellaNowEventWrapper(StellaNowBaseModel):
    key: EventKey
    value: StellaNowMessageWrapper

    @property
    def message_id(self) -> Optional[str]:
        return self.value.message_id

    @classmethod
    def create(
        cls, message: StellaNowMessageWrapper, organization_id: UUID, project_id: UUID
    ) -> "StellaNowEventWrapper":
        entity: Entity = message.primary_entity

        return cls(
            key=EventKey(
                organization_id=organization_id,
                project_id=project_id,
                entity_id=entity.entity_id,
                entity_type_definition_id=entity.entity_type_definition_id,
            ),
            value=message,
        )
