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

from requests.exceptions import ConnectTimeout, ReadTimeout

import yarf.restfullogger as logger
from yarf.authentication.base_auth import BaseAuthMethod
from access_management.backend.authsender import AuthSender
from yarf.restfulargs import RestConfig
from yarf.helpers import remove_secrets


class AMAuth(BaseAuthMethod):
    def __init__(self):
        super(AMAuth, self).__init__()
        config = RestConfig()
        config.parse()
        conf = config.get_section("AM", format='dict')
        self.logger = logger.get_logger()
        try:
            self.host = conf['host']
            self.port = conf['port']
        except KeyError as error:
            self.logger.error("Failed to find all the needed parameters. Authentication with AM not possible: {}"
                              .format(str(error)))
        self.sender = AuthSender(self.host, self.port)

    @staticmethod
    def get_info(request):
        splitted = request.full_path.split("/", 3)
        domain = splitted[1]
        domain_object = splitted[3].split("?")[0]
        return domain, domain_object

    # Returns a touple:
    #    touple[0]: true if authenticated
    #    touple[1]: the username for this request
    def get_authentication(self, request):

        try:
            domain, domain_object = self.get_info(request)
            method = request.method.upper()
        except IndexError as error:
            self.logger.error("Failed to get domain, object or method from request %s", str(error))
            return False, ""

        try:
            token = request.headers.get("X-Auth-Token", type=str)
        except KeyError:
            self.logger.error("Failed to get the authentication token from request")
            return False, ""
        parameters = {'token': token, 'domain': domain, 'domain_object': domain_object, 'method': method}
        username = ''
        try:
            response = self.sender.send_request(parameters)
            self.logger.debug(response)

            if response['username'] != '':
                username = response['username']
            if response.get('authorized', None) is not None:
                if response['authorized']:
                    self.logger.info('User {} is authorized for accessing the given domain {}'.format(response[
                                     'username'], remove_secrets(request.full_path)))
                    return True, username
                elif username != '':
                    self.logger.info('User {} is not authorized for accessing the given domain {}'.format(response[
                                     'username'], remove_secrets(request.full_path)))
                else:
                    self.logger.info('Token({}) is not valid for accessing the given domain {}'.format(token,
                                     remove_secrets(request.full_path)))
        except (ConnectTimeout, ReadTimeout) as e:
            self.logger.error('Failed to communicate with the authentication server. The following error occurred: {}'.
                              format(str(e)))
        return False, username
