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
from datetime import datetime
from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper


@pytest.fixture
def test_message():
    """Fixture providing a sample TestMessage instance."""
    class TestMessage(BaseModel):
        event_name: str
        entities: List[Dict[str, str]]
        phone_number: Dict[str, Any]
        user_id: str

    return TestMessage(
        event_name="test_event",
        entities=[{"type": "test", "id": "test_id"}],
        phone_number={"country_code": 48, "number": 700000},
        user_id="user_98888"
    )


@pytest.fixture
def organization_id():
    return "9dbc5cc1-8c36-463e-893c-b08713868e97"


@pytest.fixture
def project_id():
    return "529360a9-e40c-4d93-b3d3-5ed9f76c0037"


def test_stellanow_message_wrapper_payload(test_message, organization_id, project_id):
    """
    Test that StellaNowMessageWrapper correctly wraps a message with expected structure and payload.
    """
    # Create the wrapped message
    wrapped_message = StellaNowMessageWrapper.create(
        message=test_message,
        organization_id=organization_id,
        project_id=project_id,
    )

    # Basic structure checks
    assert isinstance(wrapped_message, StellaNowMessageWrapper), "Wrapped message should be a StellaNowMessageWrapper instance"
    assert "key" in wrapped_message.model_dump(), "Key should be present"
    assert "value" in wrapped_message.model_dump(), "Value should be present"

    # Key validation
    assert wrapped_message.key["organizationId"] == organization_id, "Organization ID mismatch"
    assert wrapped_message.key["projectId"] == project_id, "Project ID mismatch"
    assert wrapped_message.key["entityId"] == "test_id", "Entity ID should match first entity"
    assert wrapped_message.key["entityTypeDefinitionId"] == "test", "Entity type should match first entity"

    # Value validation
    assert isinstance(wrapped_message.value["payload"], str), "Payload should be a string"
    assert isinstance(wrapped_message.value["metadata"], dict), "Metadata should be a dict"

    # Payload content validation
    payload_dict = json.loads(wrapped_message.value["payload"])
    assert payload_dict["phone_number"] == {"country_code": 48, "number": 700000}, "Payload phone_number mismatch"
    assert payload_dict["user_id"] == "user_98888", "Payload user_id mismatch"
    assert "event_name" not in payload_dict, "event_name should be excluded from payload"
    assert "entities" not in payload_dict, "entities should be excluded from payload"

    # Metadata validation
    metadata = wrapped_message.value["metadata"]
    assert "messageId" in metadata, "Metadata should contain messageId"
    assert metadata["eventTypeDefinitionId"] == "test_event", "Event type mismatch"
    assert isinstance(metadata["messageOriginDateUTC"], str), "messageOriginDateUTC should be a string"
    try:
        datetime.fromisoformat(metadata["messageOriginDateUTC"].rstrip("Z"))
    except ValueError:
        pytest.fail("messageOriginDateUTC should be a valid ISO format datetime")
    assert metadata["entityTypeIds"] == [{"entityTypeDefinitionId": "test", "entityId": "test_id"}], "entityTypeIds mismatch"


def test_stellanow_message_wrapper_empty_entities(test_message, organization_id, project_id):
    """
    Test StellaNowMessageWrapper creation with no entities raises an appropriate error.
    """
    test_message.entities = []  # Simulate empty entities
    with pytest.raises(IndexError, match="list index out of range"):
        StellaNowMessageWrapper.create(
            message=test_message,
            organization_id=organization_id,
            project_id=project_id,
        )
