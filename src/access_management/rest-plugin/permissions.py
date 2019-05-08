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

from am_api_base import *


class Permissions(AMApiBase):

    """
    Permission list operations

    .. :quickref: Permissions;Permission list operations

    .. http:get:: /am/v1/permissions

    **Start Permission list**

    **Example request**:

    .. sourcecode:: http

        GET am/v1/permissions HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": ""
            "data":
            {
                "am/permissions":
                {
                    "permission_name": "am/permissions",
                    "resources": ["GET"]
                },
                "am/permissions/details":
                {
                    "permission_name": "am/permissions/details",
                    "resources": ["GET"]
                }
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: a dictionary with the permissions elements
    :> json string permission_name: Permission name
    :> json string resources: permissions resources
    """

    endpoints = ['permissions']

    def get(self):
        self.logger.info("Received a permission list request!")
        permissions_lis=dict({})
        state, permissions = self._permission_list()

        if state:
            for element in permissions:
                value = dict({})
                value.update({"permission_name": element, "resources": permissions[element]})
                permissions_lis.update({element: value})
            self.logger.info("The permission list response done!")
            return AMApiBase.embed_data(permissions_lis, 0, "")
        else:
            return AMApiBase.construct_error_response(1, permissions)

    def _permission_list(self):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                permissions = self.db.get_resources()
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "{0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, permissions
        else:
            return False, message_open
