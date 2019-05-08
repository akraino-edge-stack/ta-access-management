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


class RolesDetails(AMApiBase):

    """
    Role details operations

    .. :quickref: Roles details;Role details operations

    .. http:get:: /am/v1/roles/details

    **Start Role details**

    **Example request**:

    .. sourcecode:: http

        GET am/v1/roles/details HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
        }

    :> json string role_name: The showed role name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role details."
            "data":
            {
                "has":
                {
                    "permission_name": "has",
                    "resources": ["GET", "POST"]
                 }
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: a dictionary with the role's details
    :> json string permission_name: The permission's name.
    :> json string resources: The permission resource's.
    """

    endpoints = ['roles/details']
    parser_arguments = ['role_name']

    def get(self):
        self.logger.info("Received a role show request!")
        role_details=dict({})
        args = self.parse_args()

        state, details = self._role_show(args)

        if state:
            if len(details) == 0:
                role_details.update({"None":{"permission_name": "No permissions","resources": "None"}})
            else:
                for perm in details:
                    role_details.update({perm: {"permission_name": perm,"resources": details[perm]}})
            self.logger.info("The {0} role show response done!".format(args["role_name"]))
            return AMApiBase.embed_data(role_details, 0)
        else:
            self.logger.error("The {0} role show failed: {1}".format(args["role_name"], details))
            return AMApiBase.construct_error_response(1, details)

    def _role_show(self,args):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                details = self.db.get_role_resources(args["role_name"])
                roles = self.db.get_role_table()
                for role in roles:
                    if role["name"] == args["role_name"]:
                        break
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                self.db.close()
            return True, details
        else:
            return False, message_open
