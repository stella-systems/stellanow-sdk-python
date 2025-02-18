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
import requests


class StellaNowAuthenticationService:
    def __init__(self, authority, organization_id, api_key, api_secret):
        self.discovery_document_url = f"{authority}/realms/{organization_id}/.well-known/openid-configuration"
        self.api_key = api_key
        self.api_secret = api_secret
        self.token_response = None
        self.discovery_document = self._get_discovery_document()

    def _get_discovery_document(self):
        response = requests.get(self.discovery_document_url)
        response.raise_for_status()
        return response.json()

    def authenticate(self):
        if not self.refresh_tokens():
            self.login()

    def login(self):
        token_url = self.discovery_document['token_endpoint']
        data = {
            'client_id': 'StellaNowSDK',
            'username': self.api_key,
            'password': self.api_secret,
            'grant_type': 'password'
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.token_response = response.json()
        else:
            raise Exception("Failed to authenticate")

    def refresh_tokens(self):
        if not self.token_response:
            return False

        token_url = self.discovery_document['token_endpoint']
        data = {
            'client_id': 'StellaNowSDK',
            'refresh_token': self.token_response.get('refresh_token'),
            'grant_type': 'refresh_token'
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.token_response = response.json()
            return True
        return False

    def get_access_token(self):
        return self.token_response.get('access_token') if self.token_response else None