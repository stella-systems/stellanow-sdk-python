from typing import List, Dict, Any

from pydantic import BaseModel

from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper


def test_stellanow_message_wrapper_payload():
    class TestMessage(BaseModel):
        event_name: str
        entities: List[Dict[str, str]]
        phone_number: Dict[str, Any]
        user_id: str

    message = TestMessage(
        event_name="test_event",
        entities=[{"type": "test", "id": "test_id"}],
        phone_number={"country_code": 48, "number": 700000},
        user_id="user_98888"
    )

    wrapped_message = StellaNowMessageWrapper.create(
        message=message,
        organization_id="9dbc5cc1-8c36-463e-893c-b08713868e97",
        project_id="529360a9-e40c-4d93-b3d3-5ed9f76c0037",
        event_id="b822d187-36cb-4d53-9112-e753f45ad9af"
    )

    assert isinstance(wrapped_message.value["payload"], str)
