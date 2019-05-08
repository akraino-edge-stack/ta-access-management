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


class RolesUsers(AMApiBase):

    """
    Role list users operations

    .. :quickref: Roles users;Role list users operations

    .. http:get:: /am/v1/roles/users

    **Start Role list users**

    **Example request**:

    .. sourcecode:: http

        GET am/v1/roles/permissions HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
        }

    :> json string role_name: The role name to be searched in users.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Resource added to role"
            "data":
            {
                "has_all":
                {
                    "role_name": "has_all",
                    "users": [user1, user2]
                }
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: a dictionary with the role name and role owners
    :> json string role_name: The role name.
    :> json string users: The role owners.
    """

    endpoints = ['roles/users']
    parser_arguments = ['role_name']

    def get(self):
        self.logger.info("Received a role users request!")
        args = self.parse_args()
        result=dict({})
        state, message = self._role_users(args)

        if state:
            result.update({"role_name": args["role_name"]})
            result.update({"users": message})
            self.logger.info("The role users response done!")
            return AMApiBase.embed_data({args["role_name"]:result}, 0, "These users have this role")
        else:
            self.logger.error("The {0} roles users list creation failed: {1}".format(args["role_name"], message))
            return AMApiBase.embed_data({}, 1, message)

    def _role_users(self, args):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                users=self.db.get_role_users(args["role_name"])
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, users
        else:
            return False, message_open
