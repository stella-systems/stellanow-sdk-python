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

### TODO 

Creating these classes by hand can be prone to errors. Therefore, we provide a command line interface (CLI) tool, **StellaNow CLI**, to automate this task. This tool generates the code for the message classes automatically based on the configuration defined in the Operators Console.

You can install **StellaNow CLI** tool using pip, which is a package installer for Python. It is hosted on Python Package Index (PyPI), a repository of software for the Python programming language. To install it, open your terminal and run the following command:

```bash
pip install stellanow-cli
```

Once you have installed the **StellaNow CLI** tool, you can use it to generate message classes. Detailed instructions on how to use the **StellaNow CLI** tool can be found in the tool's documentation.

Please note that it is discouraged to write these classes yourself. Using the CLI tool ensures that the message format aligns with the configuration defined in the Operators Console and reduces the potential for errors.

## Customization

TODO 

## Support
For any issues or feature requests, feel free to create a new issue on our GitHub repository. If you need further assistance, contact our support team at help@stella.systems.

## Documentation
Detailed documentation will be available soon.

## License
This project is licensed under the terms of the MIT license.