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
import threading
import time
import paho.mqtt.client as mqtt
import os

from stellanow_sdk_python.settings import API_KEY, API_SECRET, ORGANIZATION_ID, PROJECT_ID, CLIENT_ID
from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.message_queue.lifo_message_queue import LifoMessageQueue


class StellaNowSDK:
    def __init__(self, broker_url, port, auth_service, client_id):
        self.broker_url = broker_url
        self.port = port
        self.auth_service = auth_service
        self.client_id = client_id
        self.queue = LifoMessageQueue()
        self.client = mqtt.Client(client_id)

        self.running = False
        self.connection_thread = threading.Thread(target=self._manage_connection, daemon=True)
        self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)

    def _manage_connection(self):
        while self.running:
            try:
                access_token = self.auth_service.get_access_token()
                if not access_token:
                    self.auth_service.authenticate()
                    access_token = self.auth_service.get_access_token()

                self.client.username_pw_set(self.auth_service.api_key, self.auth_service.api_secret)
                self.client.connect(self.broker_url, self.port, 60)
                self.client.loop_forever()
            except Exception as e:
                print(f"Connection error: {e}, retrying in 5 seconds")
                time.sleep(5)

    def _process_queue(self):
        while self.running:
            message = self.queue.try_dequeue()
            if message:
                self.client.publish(message['topic'], message['payload'])
                print("Message sent:", message)
            time.sleep(1)

    def send_message(self, topic, payload):
        self.queue.enqueue({"topic": topic, "payload": payload})
        print("Message queued")

    def start(self):
        self.running = True
        self.connection_thread.start()
        self.queue_thread.start()

    def stop(self):
        self.running = False
        self.client.disconnect()
        self.connection_thread.join()
        self.queue_thread.join()


if __name__ == "__main__":
    auth_service = StellaNowAuthenticationService("https://auth.example.com", ORGANIZATION_ID, API_KEY, API_SECRET)
    sdk = StellaNowSDK("mqtt.example.com", 8883, auth_service, CLIENT_ID)
    sdk.start()
    sdk.send_message("test/topic", "Hello StellaNow")
    time.sleep(10)
    sdk.stop()
