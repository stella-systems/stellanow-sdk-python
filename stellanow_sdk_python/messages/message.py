import json
import uuid
from datetime import UTC, datetime
from typing import List, Optional

from pydantic import Field

from stellanow_sdk_python.messages.base import StellaNowBaseModel


class Entity(StellaNowBaseModel):
    entity_type_definition_id: str = Field(..., serialization_alias="entityTypeDefinitionId")
    entity_id: str = Field(..., serialization_alias="entityId")


class Metadata(StellaNowBaseModel):
    message_id: Optional[str] = Field(..., serialization_alias="messageId")
    message_origin_date_utc: Optional[datetime] = Field(..., serialization_alias="messageOriginDateUTC")
    event_type_definition_id: Optional[str] = Field(..., serialization_alias="eventTypeDefinitionId")
    entity_type_ids: List[Entity] = Field(..., serialization_alias="entityTypeIds")

    @property
    def entities(self) -> List[Entity]:
        return self.entity_type_ids if self.entity_type_ids else []


class StellaNowMessageBase(StellaNowBaseModel):
    event_name: str = Field(exclude=True)
    entities: List[Entity] = Field(exclude=True)


class StellaNowMessageWrapper(StellaNowBaseModel):
    metadata: Metadata = Field(..., serialization_alias="metadata")
    payload: str = Field(..., serialization_alias="payload")

    @property
    def message_id(self) -> Optional[str]:
        return self.metadata.message_id if self.metadata and self.metadata.message_id else None

    @property
    def primary_entity(self) -> Entity:
        return self.metadata.entities[0]

    @classmethod
    def create(cls, message: StellaNowMessageBase) -> "StellaNowMessageWrapper":
        return cls.create_raw(
            event_type_definition_id=message.event_name,
            entity_types=message.entities,
            message_json=json.dumps(message.model_dump(by_alias=True)),
        )

    @classmethod
    def create_raw(
        cls, event_type_definition_id: str, entity_types: List[Entity], message_json: str
    ) -> "StellaNowMessageWrapper":
        return StellaNowMessageWrapper(
            metadata=Metadata(
                message_id=str(uuid.uuid4()),
                message_origin_date_utc=datetime.now(UTC),
                event_type_definition_id=event_type_definition_id,
                entity_type_ids=entity_types,
            ),
            payload=message_json,
        )
