# Copyright 2019 Nokia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import requests


class AuthSender(object):

    def __init__(self, host, port):
        self.url = "http://{0}:{1}/authorize/endpoint".format(host, port)
        self.headers = {'content-type': 'application/json'}
        self.counter = 0

    def send_request(self, data):
        payload = {
            "method": 'post',
            "params": json.dumps(data),
            "id": self.counter,
        }
        self.counter += 1
        return requests.post(self.url, data=json.dumps(payload), headers=self.headers, timeout=10).json()
