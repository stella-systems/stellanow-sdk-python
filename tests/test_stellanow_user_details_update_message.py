from datetime import UTC, datetime

import pytest

from stellanow_sdk_python_demo.messages.models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python_demo.messages.user_details_update_message import UserDetailsUpdateMessage


@pytest.fixture
def phone_number_model() -> PhoneNumberModel:
    """Fixture providing a PhoneNumberModel instance."""
    return PhoneNumberModel(country_code=48, number=700000)


def test_user_details_update_message_valid_cases(phone_number_model: PhoneNumberModel):
    """Test valid cases for message_origin_date_utc."""
    patron = "patron_123"
    user_id = "user_456"

    # Test with valid ISO 8601 string
    message_with_iso = UserDetailsUpdateMessage(
        patron=patron,
        user_id=user_id,
        phone_number=phone_number_model,
    )
    message_with_iso.message_origin_date_utc = "2025-04-10T22:15:10.975368Z"
    assert isinstance(message_with_iso.message_origin_date_utc, datetime)
    expected_dt = datetime.fromisoformat("2025-04-10T22:15:10.975368+00:00")
    assert message_with_iso.message_origin_date_utc == expected_dt

    # Test with valid datetime
    valid_dt = datetime.now(UTC)
    message_with_dt = UserDetailsUpdateMessage(
        patron=patron,
        user_id=user_id,
        phone_number=phone_number_model,
    )
    message_with_dt.message_origin_date_utc = valid_dt
    assert message_with_dt.message_origin_date_utc == valid_dt

    # Test without message_origin_date_utc
    message_without_date = UserDetailsUpdateMessage(
        patron=patron,
        user_id=user_id,
        phone_number=phone_number_model,
    )
    assert message_without_date.message_origin_date_utc is None


def test_user_details_update_message_invalid_timestamps(phone_number_model: PhoneNumberModel):
    """Test invalid message_origin_date_utc values."""
    patron = "patron_123"
    user_id = "user_456"

    # Create message first
    message = UserDetailsUpdateMessage(
        patron=patron,
        user_id=user_id,
        phone_number=phone_number_model,
    )

    # Test invalid formats
    test_cases = [
        ("2025-04-10T22:15:10Z", "must be in ISO 8601 format with microseconds"),  # Missing microseconds
        ("2025-04-10T22:15:10.975368", "must end with 'Z'"),  # Missing Z suffix
        ("not-a-datetime", "Invalid timestamp format"),  # Malformed string
        (1234567890, "must be a datetime object or a string"),  # Integer
    ]

    for value, error_match in test_cases:
        with pytest.raises(ValueError, match=error_match):
            message.message_origin_date_utc = value


def test_serialization_exclusions(phone_number_model: PhoneNumberModel):
    """Test that private attributes are excluded from serialization."""
    message = UserDetailsUpdateMessage(
        patron="patron_123",
        user_id="user_456",
        phone_number=phone_number_model,
    )
    message.message_origin_date_utc = "2025-04-10T22:15:10.975368Z"
    
    serialized = message.model_dump(by_alias=True)
    private_attrs = ["event_name", "entities", "message_origin_date_utc"]
    for attr in private_attrs:
        assert attr not in serialized
    
    assert set(serialized.keys()) == {"user_id", "phone_number"}
    assert serialized["user_id"] == "user_456"
    assert serialized["phone_number"] == {"number": 700000, "country_code": 48}