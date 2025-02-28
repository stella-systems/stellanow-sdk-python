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

from decouple import config

AUTH_BASE_URL = config("AUTH_BASE_URL", default="https://stella/auth")
API_KEY = config("API_KEY", default="user")
API_SECRET = config("API_SECRET", default="secret")
OIDC_CLIENT_ID = config("OIDC_CLIENT_ID", default="tools-cli")

ORGANIZATION_ID = config("ORGANIZATION_ID", default="org_id")
PROJECT_ID = config("PROJECT_ID", default="project_id")

# MQTT Settings
MQTT_BROKER_URL = config("MQTT_BROKER_URL", default="mqtt.stella")
MQTT_BROKER_PORT = config("MQTT_BROKER_PORT", default=8083, cast=int)
MQTT_KEEP_ALIVE = config("MQTT_KEEP_ALIVE", default=1, cast=int)
MQTT_CLIENT_ID = config("CLIENT_ID", default="StellaNowSDKPython")
MQTT_TOPIC = config("MQTT_TOPIC", default=f"in/{ORGANIZATION_ID}")
