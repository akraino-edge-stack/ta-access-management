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

import access_management.db.amdb as amdb
from am_api_base import *
from keystoneauth1 import exceptions


class UsersDetails(AMApiBase):

    """
    User details operations

    .. :quickref: User details;User details operations

    .. http:get:: /am/v1/users/details

    **Start User details**

    **Example request**:

    .. sourcecode:: http

        GET am/v1/users/details HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
        }

    :> json string user: The showed user's id or name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User details."
            "data":
            {
                "616de2097d1647e88bdb83bfd9fdbedf":
                {
                    "default_project_id": "5dfb6baff51a4e10ab98e262e6f3f59d",
                    "domain_id": "default",
                    "email": "None",
                    "enabled": true,
                    "id": "616de2097d1647e88bdb83bfd9fdbedf",
                    "links":
                    {
                        "self": "http://192.168.1.7:5000/v3/users/616de2097d1647e88bdb83bfd9fdbedf"
                    },
                    "name": "um_admin",
                    "options": {},
                    "password_expires_at": null,
                    "roles": [ "infrastructure_admin", "basic_member" ]
                }
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: the user details
    :> json string default_project_id: The user's default project id.
    :> json string domain_id: The user's domain id.
    :> json string email: The user's e-mail.
    :> json string enabled: The user's locking state.
    :> json string id: The user's id.
    :> json string links: The user's url address.
    :> json string name: The user's name.
    :> json string options: The user's options.
    :> json string password_expires_at: The user's password expiration date.
    :> json string roles: The user's roles.
    """

    endpoints = ['users/details']
    parser_arguments = ['user']

    def get(self):
        self.logger.info("Received a user show request!")
        args = self.parse_args()

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            state, user_details = self.collect_user_details(user_info)
            if state:
                self.logger.info("User show response done!")
                return AMApiBase.embed_data({user_info["id"]: user_details}, 0, "User details.")
            else:
                self.logger.error(user_details)
                return AMApiBase.embed_data({}, 1, user_details)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def collect_user_details(self, user_info):
        try:
            s_user = self.keystone.users.get(user_info["id"])
        except exceptions.http.NotFound as ex:
            self.logger.error("{0}".format(ex))
            return False, "This user does not exist in the keystone!"
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)

        state, roles = self.ask_user_roles(user_info)
        if state:
            s_user = s_user._info
            if 'email' not in s_user:
                s_user["email"] = None
            if 'description' not in s_user:
                s_user["description"] = None
            if roles == None:
                s_user["roles"] = "The {0} user does not exist in the AM database!".format(user_info["name"])
            else:
                s_user["roles"] = roles
            return True, s_user
        else:
            return False, roles

    def ask_user_roles(self, user_info):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                s_user_db = self.db.get_user_roles(user_info["id"])
            except amdb.NotExist:
                self.logger.info ("The {0} user does not exist in the AM database!".format(user_info["id"]))
                s_user_db = None
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, ex
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, s_user_db
        else:
            return False, message_open
