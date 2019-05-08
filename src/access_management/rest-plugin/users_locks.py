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
from am_api_base import *
from keystoneauth1 import exceptions
from cmframework.apis import cmclient


class UserLock(AMApiBase):

    """
    User lock operations

    .. :quickref: User lock;User lock operations

    .. http:post:: /am/v1/users/locks

    **Start User lock**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users/locks HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
        }

    :> json string user: The locked user's id or name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User locked success."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    User unlock operations

    .. :quickref: User lock;User unlock operations

    .. http:delete:: /am/v1/users/locks

    **Start User unlock**

    **Example request**:

    .. sourcecode:: http

        DELETE am/v1/users/locks HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
        }

    :> json string user: The unlocked user's id or name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User unlocked!"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users/locks']
    parser_arguments = ['user']

    def post(self):
        self.logger.info("Received a user lock request!")
        args = self.parse_args()

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            status, message = self._lock_user(user_info)

            if status:
                self.logger.info("User {0} locked".format(user_info["name"]))
                return AMApiBase.embed_data({}, 0, "User locked.")
            else:
                self.logger.error("User {0} lock failed: {1}".format(user_info["name"], message))
                return AMApiBase.embed_data({}, 1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def delete(self):
        self.logger.info("Received a user unlock request!")
        args = self.parse_args()

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            status, message = self._unlock_user(user_info)

            if status:
                self.logger.info("User {0} unlocked!".format(user_info["name"]))
                return AMApiBase.embed_data({}, 0, "User unlocked!")
            else:
                self.logger.error("User {0} unlock failed: {1}".format(user_info["name"], message))
                return AMApiBase.embed_data({}, 1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def _unlock_user(self, user_info):
         try:
             self.keystone.users.update(user_info["id"], enabled=True)
         except exceptions.http.NotFound as ex:
             self.logger.error("{0}".format(ex))
             return False, "This user does not exist in the keystone!"
         except Exception as ex:
             self.logger.error("{0}".format(ex))
             return False, "{0}".format(ex)
         return self.user_checker(user_info, "-u")

    def _lock_user(self, user_info):
        try:
            self.keystone.users.update(user_info["id"], enabled=False)
        except exceptions.http.NotFound as ex:
            self.logger.error("{0}".format(ex))
            return False, "This user does not exist in the keystone!"
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)
        return self.user_checker(user_info, "-l")

    def user_checker(self, user_info, user_state):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_user_roles(user_info["id"])
                self.logger.debug("Check the chroot role, when locking the user!")
                for role in roles:
                    self.logger.debug("Role name: {0}".format(role))
                    if self.db.is_chroot_role(role):
                        self.logger.debug("Found a chroot role attached to the {0} user!".format(user_info["name"]))
                        self.lock_state_handler(user_info["name"], "Chroot", "cloud.chroot", user_state)
                    if role == "linux_user":
                        self.logger.debug("Found a Linux role attached to the {0} user!".format(user_info["name"]))
                        self.lock_state_handler(user_info["name"], "Linux", "cloud.linuxuser", user_state)
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, ""
        else:
            return False, message_open

    def lock_state_handler(self, username, user_type, list_name, state):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        if user_list is not None:
            self.logger.debug("The {0} user list exists!".format(user_type))
            for val in user_list:
                if val["name"] == username:
                    val["lock_state"] = state
                    break
            self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
            cmc.set_property(list_name, json.dumps(user_list))
