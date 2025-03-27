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
from typing import Dict

import pytest

from stellanow_sdk_python.messages.message_base import EntityType, StellaNowMessageBase
from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper


@pytest.fixture
def test_message():
    """Fixture providing a sample TestMessage instance with EntityType-based entities.

    Returns:
        TestMessage: A configured instance of the TestMessage class.
    """
    class TestMessage(StellaNowMessageBase):
        phone_number: Dict[str, int]  # Simplified for testing; replace with PhoneNumberModel if needed
        user_id: str

        def to_json(self) -> Dict:
            """Serialize the message fields to a dictionary, excluding entity-related fields."""
            return {
                "phone_number": self.phone_number,
                "user_id": self.user_id
            }

    return TestMessage(
        event_name="test_event",
        entities=[EntityType(entityTypeDefinitionId="test", entityId="test_id")],
        phone_number={"country_code": 48, "number": 700000},
        user_id="user_98888"
    )


@pytest.fixture
def organization_id():
    """Fixture providing a sample organization ID.

    Returns:
        str: A UUID string representing the organization ID.
    """
    return "9dbc5cc1-8c36-463e-893c-b08713868e97"


@pytest.fixture
def project_id():
    """Fixture providing a sample project ID.

    Returns:
        str: A UUID string representing the project ID.
    """
    return "529360a9-e40c-4d93-b3d3-5ed9f76c0037"


def test_stellanow_message_wrapper_full_structure(test_message, organization_id, project_id):
    """Test that StellaNowMessageWrapper creates a fully structured message with correct key, value, metadata, and payload.

    This test validates the entire structure of the wrapped message, ensuring all fields are present,
    correctly formatted, and match the expected values based on the input message.

    Args:
        test_message (TestMessage): The sample message instance to wrap.
        organization_id (str): The organization ID for the wrapper key.
        project_id (str): The project ID for the wrapper key.
    """
    # Create the wrapped message
    wrapped_message = StellaNowMessageWrapper.create(
        message=test_message,
        organization_id=organization_id,
        project_id=project_id,
    )

    # Validate instance type
    assert isinstance(wrapped_message, StellaNowMessageWrapper), "Wrapped message must be a StellaNowMessageWrapper instance"

    # Full key structure validation
    expected_key = {
        "organizationId": organization_id,
        "projectId": project_id,
        "entityId": "test_id",
        "entityTypeDefinitionId": "test"
    }
    assert wrapped_message.key == expected_key, f"Key structure mismatch. Expected {expected_key}, got {wrapped_message.key}"

    # Full value structure validation
    value = wrapped_message.value
    assert set(value.keys()) == {"metadata", "payload"}, "Value must contain only 'metadata' and 'payload' keys"
    assert isinstance(value["payload"], str), "Payload must be a string"
    assert isinstance(value["metadata"], dict), "Metadata must be a dictionary"

    # Payload validation
    payload_dict = json.loads(value["payload"])
    expected_payload = {
        "phone_number": {"country_code": 48, "number": 700000},
        "user_id": "user_98888"
    }
    assert payload_dict == expected_payload, f"Payload mismatch. Expected {expected_payload}, got {payload_dict}"

    # Metadata validation
    metadata = value["metadata"]
    expected_metadata_keys = {"messageId", "messageOriginDateUTC", "eventTypeDefinitionId", "entityTypeIds"}
    assert set(metadata.keys()) == expected_metadata_keys, f"Metadata keys mismatch. Expected {expected_metadata_keys}, got {set(metadata.keys())}"
    assert isinstance(metadata["messageId"], str), "messageId must be a string"
    assert len(metadata["messageId"]) == 36, "messageId should be a UUID (36 characters)"
    assert metadata["eventTypeDefinitionId"] == "test_event", "Event type mismatch"
    assert isinstance(metadata["messageOriginDateUTC"], str), "messageOriginDateUTC must be a string"
    try:
        datetime.fromisoformat(metadata["messageOriginDateUTC"].rstrip("Z"))
    except ValueError:
        pytest.fail("messageOriginDateUTC must be a valid ISO format datetime")
    expected_entity_type_ids = [{"entityTypeDefinitionId": "test", "entityId": "test_id"}]
    assert metadata["entityTypeIds"] == expected_entity_type_ids, f"entityTypeIds mismatch. Expected {expected_entity_type_ids}, got {metadata['entityTypeIds']}"


def test_stellanow_message_wrapper_empty_entities(test_message, organization_id, project_id):
    """Test that StellaNowMessageWrapper raises an error when created with a message having no entities.

    This test ensures that the wrapper fails gracefully when the input message lacks entities,
    as the key construction depends on at least one entity being present.

    Args:
        test_message (TestMessage): The sample message instance to modify and wrap.
        organization_id (str): The organization ID for the wrapper key.
        project_id (str): The project ID for the wrapper key.

    Raises:
        IndexError: If the entities list is empty, indicating an invalid message state.
    """
    test_message.entities = []  # Simulate empty entities
    with pytest.raises(IndexError, match="list index out of range"):
        StellaNowMessageWrapper.create(
            message=test_message,
            organization_id=organization_id,
            project_id=project_id,
        )
