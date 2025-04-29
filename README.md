# StellaNowPythonSDK

## Introduction
Welcome to the StellaNow Python SDK. This SDK is designed to provide an easy-to-use interface for developers integrating their Python applications with the StellaNow Platform. The SDK communicates with the StellaNow Platform using the MQTT protocol over secure WebSockets or TCP, depending on the configuration.

## Key Features
- Automated connection handling (connection, disconnection, and reconnection)
- Message queuing to handle any network instability
- Authentication management (login and automatic token refreshing)
- Easy interface to send different types of messages
- Extensibility options for more specific needs

## Getting Started
Before you start integrating the SDK, ensure you have a Stella Now account.

## Installation
To integrate the StellaNowSDK into your project, follow these steps:

### Via pip
The easiest way to add the StellaNowSDK to your project is through pip, the Python package installer. Install the package from PyPI ([stellanow-sdk-python](https://pypi.org/project/stellanow-sdk-python/)) by running the following command in your terminal:
```bash
pip install stellanow-sdk-python
```

## Configuration
The SDK supports multiple authentication strategies when connecting to the Stella Now MQTT Sink. You can configure the SDK using OIDC authentication, username/password authentication, or no authentication, depending on your environment.

### MQTT Broker URL
The SDK uses an MQTT URL to connect to the StellaNow Platform or a local broker. The URL scheme dictates the transport and TLS settings:

- mqtt or mqtt-tcp: TCP transport, no TLS (default port: 1883).
- mqtts: TCP transport with TLS (default port: 8883).
- ws: WebSockets transport, no TLS (default port: 80).
- wss: WebSockets transport with TLS (default port: 443).

Each configuration function (e.g., `configure_dev_oidc_mqtt_fifo_sdk`) uses a default URL tailored to its environment (development, production, or local).


### Setting Up StellaNow SDK
To use the SDK, first ensure you have set the necessary environment variables:
- ORGANIZATION_ID
- PROJECT_ID
- For `OIDC`: OIDC_USERNAME, OIDC_PASSWORD
- For `Username/Password`: MQTT_USERNAME, MQTT_PASSWORD

Then, configure the SDK with the appropriate authentication strategy.

### Using OIDC Authentication
To authenticate with `StellaNow's` OIDC (OpenID Connect) on DEV environment using FIFO order, use `configure_dev_oidc_mqtt_fifo_sdk`:

```python
from stellanow_sdk_python.configure_sdk import configure_dev_oidc_mqtt_fifo_sdk

async def main():
    sdk = configure_dev_oidc_mqtt_fifo_sdk()
    await sdk.start()
```

This will:
* Authenticate with OIDC using the provided username and password, using a specific OIDC Client designed for data ingestion.
* Resulting token will be used in MQTT broker authentication with specific claim.
* Connect to the MQTT sink securely.

### Using Username/Password Authentication
For scenarios requiring simple username/password authentication, use `configure_dev_basic_mqtt_lifo_sdk`:
```python
from stellanow_sdk_python.configure_sdk import configure_dev_basic_mqtt_lifo_sdk

async def main():
    sdk = configure_dev_basic_mqtt_lifo_sdk()
    await sdk.start()
```

This will:
- Use the USERNAME and PASSWORD environment variables for MQTT broker authentication.
- Connect to the MQTT sink with the specified transport and TLS settings.

### Using No Authentication
For local development or scenarios where authentication is not required, use configure_local_nanomq_basic_mqtt_fifo_sdk or configure_prod_none_mqtt_fifo_sdk:

```python
from stellanow_sdk_python.configure_sdk import configure_prod_none_mqtt_fifo_sdk

async def main():
    sdk = configure_prod_none_mqtt_fifo_sdk()
    await sdk.start()
```

This will:
- Connect to the MQTT sink without authentication (or with dummy credentials for local testing).
- Be useful for testing against local MQTT brokers like NanoMQ.

Ensure you have set the appropriate environment variables.

> **Note:** The client_id used in the MQTT connection must be unique per connection. If two connections use the same client_id, the first connection will be dropped. To prevent conflicts, the SDK automatically generates a unique client_id at startup in the format StellaNowSDKPython__<10-char-nanoid>. You can find the generated value in the logs:
```python
2025-03-14 13:18:36.802 | INFO     | stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink:__init__:67 - SDK Client ID is "StellaNowSDKPython_oLMA971RWD"
```

## Sample Application
Here is a simple application that uses StellaNowSDK to send user details messages to the Stella Now platform.

This script is the main entry point for our demonstration. The main function does a few things:
- It establishes a connection to StellaNow.
- It creates a UserDetailsMessage and sends it using the StellaNow SDK.
- It checks and logs the queue status.
- Finally, it disconnects from StellaNow.
```python
import asyncio
import sys
from stellanow_sdk_python.configure_sdk import configure_dev_oidc_mqtt_fifo_sdk
from stellanow_sdk_python_demo.messages.models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python_demo.messages.user_details_update_message import UserDetailsUpdateMessage
from loguru import logger

async def main():
    """Main entry point for the StellaNow SDK demo."""
    sdk = configure_dev_oidc_mqtt_fifo_sdk()
    shutdown_event = asyncio.Event()  # Event to signal shutdown

    try:
        await sdk.start()
        for i in range(10):
            message = UserDetailsUpdateMessage(
                patron="12345", user_id=f"user_{i}", phone_number=PhoneNumberModel(country_code=44, number=753594 + i)
            )
            logger.info(f"Sending message {i + 1}...")
            await sdk.send_message(message)
            await asyncio.sleep(2)
        logger.info("Initial messages sent. Keeping SDK alive...")
        await shutdown_event.wait()  # Wait indefinitely until shutdown
    
    except KeyboardInterrupt:
        logger.warning("Received Ctrl+C, shutting down gracefully...")
        shutdown_event.set()  # Signal shutdown
        await sdk.stop()
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        await sdk.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### Setting the Message Origin Timestamp

The `message_origin_date_utc` field in a `StellaNowMessageBase`-derived message specifies the UTC timestamp when the message was created. This field is optional but highly recommended for accurate event tracking and auditing in the StellaNow Platform. The timestamp must be in ISO 8601 format with microseconds and a `Z` suffix (e.g., `2025-04-25T12:34:56.789012Z`) when serialized.

#### Requirements
- **Type**: Python `datetime` object or ISO 8601 string.
- **Format**: If provided as a string, it must include microseconds and end with `Z` (e.g., `2025-04-25T12:34:56.789012Z`).
- **Timezone**: Must represent UTC time. Non-UTC `datetime` objects will raise a validation error.
- **Validation**: The SDK validates the timestamp to ensure it meets these requirements. Invalid formats will raise a `ValueError`.

#### Setting `message_origin_date_utc`
Set `message_origin_date_utc` after creating a message by assigning a `datetime` object or a valid ISO 8601 string to the `message_origin_date_utc` property. If not set, the field remains `None` in the message object, but the SDK automatically assigns the current UTC time when the message is wrapped in a `StellaNowMessageWrapper` (e.g., during `sdk.send_message`).
```python
import asyncio
import sys
from stellanow_sdk_python.configure_sdk import configure_dev_oidc_mqtt_fifo_sdk
from stellanow_sdk_python_demo.messages.models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python_demo.messages.user_details_update_message import UserDetailsUpdateMessage
from loguru import logger

async def main():
    """Main entry point for the StellaNow SDK demo."""
    sdk = configure_dev_oidc_mqtt_fifo_sdk()
    shutdown_event = asyncio.Event()  # Event to signal shutdown

    try:
        await sdk.start()
        for i in range(10):
            message = UserDetailsUpdateMessage(
                patron="12345", user_id=f"user_{i}", phone_number=PhoneNumberModel(country_code=44, number=753594 + i)
            )
            message.message_origin_date_utc = "2025-04-25T12:34:56.789012Z"
            logger.info(f"Sending message {i + 1}...")
            await sdk.send_message(message)
            await asyncio.sleep(2)
        logger.info("Initial messages sent. Keeping SDK alive...")
        await shutdown_event.wait()  # Wait indefinitely until shutdown
    
    except KeyboardInterrupt:
        logger.warning("Received Ctrl+C, shutting down gracefully...")
        shutdown_event.set()  # Signal shutdown
        await sdk.stop()
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        await sdk.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

The full code for the sample application can be found here:
- [Basic Application](stellanow_sdk_python_demo/main.py)

### IMPORTANT

> **`stop` METHOD USAGE**
>
>The stop method in the StellaNowSDK is asynchronous and stops the SDK's message processing immediately. When called as await sdk.stop(), it halts the processing of the message queue and disconnects from the MQTT broker.
>
>This behavior can have important consequences when using non-persistent queue implementations (like the default in-memory FIFO or LIFO queues). Any messages that have been added to the queue but not yet sent will remain unsent until start is called again.
>
>If your application shuts down before start is called again, those unsent messages will be lost because non-persistent queues do not store their contents when the application terminates.

## Message Formatting
Messages in StellaNowSDK are wrapped in a StellaNowEventWrapper, and each specific message type extends this class to define its own properties. Each message needs to follow a certain format, including a type, list of entities, and optional fields. Here is an example:

```python
from pydantic import Field
from stellanow_sdk_python_demo.messages.models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python.messages.message import Entity, StellaNowMessageBase


class UserDetailsUpdateMessage(StellaNowMessageBase):
    user_id: str = Field(None, serialization_alias="user_id")
    phone_number: PhoneNumberModel = Field(None, serialization_alias="phone_number")

    def __init__(self, patron: str, user_id: str, phone_number: PhoneNumberModel):
        super().__init__(
            event_name="user_details_update",
            entities=[Entity(entity_type_definition_id="patron", entity_id=patron)],
            user_id=user_id,
            phone_number=phone_number,
        )
 ```

Creating these classes by hand can be prone to errors. Therefore, we provide a command line interface (CLI) tool, [stellanow-cli](https://pypi.org/project/stellanow-cli/), to automate this task. This tool generates the code for the message classes automatically based on the configuration defined in the Operators Console.

You can install the StellaNow CLI tool using pip:
```bash
pip install stellanow-cli
```
Once you have installed the **StellaNow CLI** tool, you can use it to generate message classes. Detailed instructions on how to use the **StellaNow CLI** tool can be found in the tool's documentation.

Please note that it is discouraged to write these classes yourself. Using the CLI tool ensures that the message format aligns with the configuration defined in the Operators Console and reduces the potential for errors.

## Customization

StellaNowSDK provides extensive flexibility for developers to adapt the SDK to their specific needs. You can extend key components, including message queuing strategies, sinks (where messages are sent), connection strategies, and authentication mechanisms.

### Customizing the Message Queue Strategy
By default, `StellaNowPythonSDK` uses an in-memory queue to temporarily hold messages before sending them to a sink. These non-persistent queues will lose all messages if the application terminates unexpectedly.

If your application requires a persistent queue that survives restarts or crashes, you can implement a custom queue strategy by extending `IMessageQueueStrategy` and integrating it with a database, file system, or distributed queu

>⚠️ **Performance Considerations:** Persistent queues introduce additional latency and require careful design to balance reliability and performance.

#### Adding a Custom Sink & Connection Strategy
A sink is where messages are ultimately delivered. StellaNowSDK supports MQTT-based sinks, but you can extend this to support Kafka, Webhooks, Databases, or any custom integration.

Each sink is paired with a connection strategy, which determines how it establishes a connection. You can implement a custom connection strategy for different protocols or authentication mechanisms.

##### Example: Adding a Custom Sink
To add a new sink, implement `IStellaNowSink` and update configure_sdk.py:
```python
from stellanow_sdk_python.sinks.custom_sink import CustomSink

mqtt_sink = CustomSink(auth_strategy=auth_strategy, env_config=env_config, project_info=project_info)
```
##### Extending the Authentication Service
StellaNowSDK supports multiple authentication mechanisms, including:
- OIDC-based authentication
- Username/password authentication
- No authentication

If your project requires a new authentication mechanism, implement IMqttAuthStrategy and register it in configure_sdk.py:

```python
from stellanow_sdk_python.sinks.mqtt.auth_strategy.custom_auth_strategy import CustomAuthStrategy

auth_strategy = CustomAuthStrategy(project_info, credentials, env_config)
```
> ⚠️ **Security Considerations:** Ensure your authentication mechanism is properly secured and does not expose credentials in logs or configuration files.

## Support
For any issues or feature requests, feel free to create a new issue on our GitHub repository. If you need further assistance, contact our support team at help@stella.systems.

## Documentation
Detailed documentation will be available soon.

## License
This project is licensed under the terms of the MIT license.