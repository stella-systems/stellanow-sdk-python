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
import pytest
import uuid

from datetime import datetime
from pydantic import Field
from typing import Dict

from stellanow_sdk_python.messages.base import StellaNowBaseModel
from stellanow_sdk_python.messages.message import Entity, StellaNowMessageBase, StellaNowMessageWrapper, Metadata
from stellanow_sdk_python.messages.event import StellaNowEventWrapper, EventKey


@pytest.fixture
def organization_id() -> str:
    """Fixture providing a sample organization ID."""
    return "9dbc5cc1-8c36-463e-893c-b08713868e97"


@pytest.fixture
def project_id() -> str:
    """Fixture providing a sample project ID."""
    return "529360a9-e40c-4d93-b3d3-5ed9f76c0037"


@pytest.fixture
def test_message() -> StellaNowMessageBase:
    class PhoneNumber(StellaNowBaseModel):
        number: int = Field(..., serialization_alias="number")
        country_code: int = Field(..., serialization_alias="country_code")

    class TestMessage(StellaNowMessageBase):
        phone_number: PhoneNumber = Field(..., serialization_alias="phone_number")
        user_id: str = Field(..., serialization_alias="user_id")

    return TestMessage(
        phone_number=PhoneNumber(country_code=48, number=700000),
        user_id="user_98888",
        event_name="test_event",
        entities=[Entity(entity_type_definition_id="test", entity_id="test_id")]
    )


@pytest.fixture
def message_wrapper(test_message: StellaNowMessageBase) -> StellaNowMessageWrapper:
    """Fixture providing a StellaNowMessageWrapper instance."""
    return StellaNowMessageWrapper.create(test_message)


def test_stellanow_message_wrapper_create(test_message: StellaNowMessageBase):
    """Test the create method of StellaNowMessageWrapper."""
    wrapped_message = StellaNowMessageWrapper.create(test_message)

    # Validate instance type
    assert isinstance(wrapped_message, StellaNowMessageWrapper), "Must return a StellaNowMessageWrapper instance"

    # Validate metadata
    metadata = wrapped_message.metadata
    assert isinstance(metadata, Metadata), "Metadata must be a Metadata instance"
    assert isinstance(metadata.message_id, str), "message_id must be a string"
    try:
        uuid.UUID(metadata.message_id, version=4)
    except ValueError:
        pytest.fail("message_id must be a valid UUID v4")
    assert isinstance(metadata.message_origin_date_utc, datetime), "message_origin_date_utc must be a datetime"
    assert metadata.event_type_definition_id == "test_event", "Event type mismatch"
    assert metadata.entity_type_ids == test_message.entities, "Entities mismatch"

    # Validate payload
    payload_dict = json.loads(wrapped_message.payload)
    expected_payload = {
        "phone_number": {"country_code": 48, "number": 700000},
        "user_id": "user_98888",
    }
    assert payload_dict == expected_payload, f"Payload mismatch. Expected {expected_payload}, got {payload_dict}"

    # Validate message_id property
    assert wrapped_message.message_id == metadata.message_id, "message_id property must match metadata.message_id"


def test_stellanow_message_wrapper_create_raw():
    """Test the create_raw method of StellaNowMessageWrapper."""
    entities = [Entity(entity_type_definition_id="test", entity_id="test_id")]
    message_json = json.dumps({"test": "data"})
    wrapped_message = StellaNowMessageWrapper.create_raw(
        event_type_definition_id="test_event",
        entity_types=entities,
        message_json=message_json
    )

    # Validate instance type
    assert isinstance(wrapped_message, StellaNowMessageWrapper), "Must return a StellaNowMessageWrapper instance"

    # Validate metadata
    metadata = wrapped_message.metadata
    assert isinstance(metadata.message_id, str), "message_id must be a string"
    assert isinstance(metadata.message_origin_date_utc, datetime), "message_origin_date_utc must be a datetime"
    assert metadata.event_type_definition_id == "test_event", "Event type mismatch"
    assert metadata.entity_type_ids == entities, "Entities mismatch"

    # Validate payload
    assert wrapped_message.payload == message_json, "Payload must match input"


def test_stellanow_event_wrapper_full_structure(
    message_wrapper: StellaNowMessageWrapper, organization_id: str, project_id: str
):
    """Test the full structure of StellaNowEventWrapper."""
    event_wrapper = StellaNowEventWrapper.create(
        message=message_wrapper,
        organization_id=organization_id,
        project_id=project_id
    )

    # Validate instance type
    assert isinstance(event_wrapper, StellaNowEventWrapper), "Must return a StellaNowEventWrapper instance"

    # Validate key
    assert isinstance(event_wrapper.key, EventKey), "Key must be an EventKey instance"
    expected_key = {
        "organizationId": organization_id,
        "projectId": project_id,
        "entityId": "test_id",
        "entityTypeDefinitionId": "test"
    }
    key_dict = event_wrapper.key.model_dump(by_alias=True)
    assert key_dict == expected_key, f"Key mismatch. Expected {expected_key}, got {key_dict}"

    # Validate value
    assert event_wrapper.value == message_wrapper, "Value must match the input message wrapper"

    # Validate message_id property
    assert event_wrapper.message_id == message_wrapper.message_id, "message_id must match the wrapped message's message_id"

    # Validate serialization
    serialized = event_wrapper.model_dump(by_alias=True)
    print(serialized)
    assert set(serialized.keys()) == {"key", "value"}, "Serialized output must contain only 'key' and 'value'"
    assert serialized["key"] == expected_key, "Serialized key mismatch"
    metadata = serialized["value"]["metadata"]
    assert metadata["messageOriginDateUTC"].endswith("Z"), "messageOriginDateUTC must end with 'Z'"
    try:
        datetime.fromisoformat(metadata["messageOriginDateUTC"].rstrip("Z"))
    except ValueError:
        pytest.fail("messageOriginDateUTC must be a valid ISO format datetime")


def test_stellanow_message_wrapper_serialization_exclusions(test_message: StellaNowMessageBase):
    """Test that private attributes are excluded from serialization."""
    wrapped_message = StellaNowMessageWrapper.create(test_message)
    serialized = wrapped_message.model_dump(by_alias=True)

    # Private attributes should not be in the serialized output
    assert "event_name" not in serialized, "Private attribute 'event_name' must be excluded"
    assert "entities" not in serialized, "Private attribute 'entities' must be excluded"

    # Validate expected fields
    assert set(serialized.keys()) == {"metadata", "payload"}, "Serialized output must contain only 'metadata' and 'payload'"


def test_stellanow_message_wrapper_optional_fields():
    """Test handling of optional fields in Metadata."""
    entities = [Entity(entity_type_definition_id="test", entity_id="test_id")]
    message_json = json.dumps({"test": "data"})
    wrapped_message = StellaNowMessageWrapper(
        metadata=Metadata(
            message_id=None,
            message_origin_date_utc=None,
            event_type_definition_id=None,
            entity_type_ids=entities
        ),
        payload=message_json
    )

    # Validate serialization
    serialized = wrapped_message.model_dump(by_alias=True)
    assert serialized["metadata"]["messageId"] is None, "messageId should be None"
    assert serialized["metadata"]["messageOriginDateUTC"] is None, "messageOriginDateUTC should be None"
    assert serialized["metadata"]["eventTypeDefinitionId"] is None, "eventTypeDefinitionId should be None"

    # Validate message_id property
    assert wrapped_message.message_id is None, "message_id should be None when metadata.message_id is None"
