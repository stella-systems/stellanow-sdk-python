import json
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, PrivateAttr

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
    _message_origin_date_utc: Optional[datetime] = PrivateAttr(default=None)

    def __init__(self, **data: Dict[str, Any]) -> None:
        # Handle message_origin_date_utc during initialization
        message_origin_date_utc = data.pop("message_origin_date_utc", None)
        super().__init__(**data)
        if message_origin_date_utc is not None:
            self.message_origin_date_utc = message_origin_date_utc

    @classmethod
    def _validate_timestamp(cls, value: Union[datetime, str]) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                if not value.endswith("Z"):
                    raise ValueError("Timestamp must end with 'Z'")
                if "." not in value.split("T")[1]:
                    raise ValueError("Timestamp must be in ISO 8601 format with microseconds")
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {str(e)}")
        raise ValueError("message_origin_date_utc must be a datetime object or a string")

    @property
    def message_origin_date_utc(self) -> Optional[datetime]:
        return self._message_origin_date_utc

    @message_origin_date_utc.setter
    def message_origin_date_utc(self, value: Optional[Union[datetime, str]]) -> None:
        if value is None:
            self._message_origin_date_utc = None
        else:
            self._message_origin_date_utc = self._validate_timestamp(value)


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
    def create(
        cls,
        message: StellaNowMessageBase,
    ) -> "StellaNowMessageWrapper":
        return cls.create_raw(
            event_type_definition_id=message.event_name,
            entity_types=message.entities,
            message_json=json.dumps(message.model_dump(by_alias=True)),
            message_origin_date_utc=message.message_origin_date_utc,
        )

    @classmethod
    def create_raw(
        cls,
        event_type_definition_id: str,
        entity_types: List[Entity],
        message_json: str,
        message_origin_date_utc: Optional[datetime] = None,
    ) -> "StellaNowMessageWrapper":
        return StellaNowMessageWrapper(
            metadata=Metadata(
                message_id=str(uuid.uuid4()),
                message_origin_date_utc=message_origin_date_utc or datetime.now(UTC),
                event_type_definition_id=event_type_definition_id,
                entity_type_ids=entity_types,
            ),
            payload=message_json,
        )
