# StellaNowSDK
## Introduction
Welcome to the StellaNow Python SDK. This SDK is designed to provide an easy-to-use interface for developers integrating their Python applications with the StellaNow Platform. The SDK communicates with the StellaNow Platform using the MQTT protocol over secure WebSockets.

## Key Features
* Automated connection handling (connection, disconnection and reconnection)
* Message queuing to handle any network instability
* Authentication management (login and automatic token refreshing)
* Easy interface to send different types of messages
* Per-message callbacks for notification of successful message sending
* Extensibility options for more specific needs

## Getting Started
Before you start integrating the SDK, ensure you have a Stella Now account and valid API credentials which include **OrganizationId**, **ApiKey**, and **ApiSecret**.

## Installation
To integrate the StellaNowSDK into your project, follow these steps:
```bash
pip install stellanow-sdk-python
```

Creating these classes by hand can be prone to errors. Therefore, we provide a command line interface (CLI) tool, **StellaNow CLI**, to automate this task. This tool generates the code for the message classes automatically based on the configuration defined in the Operators Console.

You can install **StellaNow CLI** tool using pip, which is a package installer for Python. It is hosted on Python Package Index (PyPI), a repository of software for the Python programming language. To install it, open your terminal and run the following command:

```bash
pip install stellanow-cli
```

Once you have installed the **StellaNow CLI** tool, you can use it to generate message classes. Detailed instructions on how to use the **StellaNow CLI** tool can be found in the tool's documentation.

Please note that it is discouraged to write these classes yourself. Using the CLI tool ensures that the message format aligns with the configuration defined in the Operators Console and reduces the potential for errors.

## Usage
Run the CLI to generate message classes:
stellanow-cli generate-messages --config your-config.yaml --output stellanow_sdk_python_demo/models
See the StellaNow CLI documentation (https://github.com/stellatechnologies/stellanow-cli) for details. Avoid writing message classes by hand to ensure compatibility and reduce errors.

### Customization
The SDK offers pre-defined configurations in stellanow_sdk_python/configure_sdk.py for common setups:
- configure_dev_oidc_mqtt_fifo_sdk(): Dev environment, OIDC auth, MQTT sink, FIFO queue.
- configure_sdev_username_mqtt_fifo_sdk(): Dev environment, username/password auth, MQTT sink, FIFO queue.
- configure_prod_none_mqtt_fifo_sdk(): Prod environment, no auth, MQTT sink, FIFO queue.

Example usage in stellanow_sdk_python_demo/main.py:
from stellanow_sdk_python.config import configure_dev_oidc_mqtt_fifo_sdk

sdk = configure_dev_oidc_mqtt_fifo_sdk()
await sdk.start()

To create custom configs:
1. Modify config.py to add new configure_* functions with your preferred auth_strategy_type, env_config, and queue_strategy_type.
2. Extend queue_strategies in configure_sdk for additional queue types (e.g., LIFO).

### Demo
The stellanow_sdk_python_demo/main.py script showcases SDK usage:
- Initializes with a pre-defined config (e.g., OIDC, MQTT, FIFO).
- Sends sample UserDetailsMessage events.
- Handles shutdown gracefully.

Run it with correct credentials to see it in action!
## Support
For any issues or feature requests, feel free to create a new issue on our GitHub repository. If you need further assistance, contact our support team at help@stella.systems.

## Documentation
Detailed documentation will be available soon.

## License
This project is licensed under the terms of the MIT license.