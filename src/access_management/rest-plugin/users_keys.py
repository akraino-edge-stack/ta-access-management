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
from cmframework.apis import cmclient


class UsersKeys(AMApiBase):

    """
    User add key operations

    .. :quickref: User keys;User add key operations

    .. http:post:: /am/v1/users/keys

    **Start User add key**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users/keys HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
            "key": <user key>
        }

    :> json string user: The user's id or name.
    :> json string key: The user's public key.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User public key uploaded!"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    User remove key operations

    .. :quickref: User keys;User remove key operations

    .. http:delete:: /am/v1/users/keys

    **Start User remove key**

    **Example request**:

    .. sourcecode:: http

        DELETE am/v1/users/keys HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
        }

    :> json string user: The user's id or name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User public key removed!"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users/keys']
    parser_arguments = ['user',
                        'key']

    def post(self):
        self.logger.info("Received an add key request!")
        args = self.parse_args()

        if args["key"] is None:
            self.logger.error("The public key is missing!")
            return AMApiBase.embed_data({}, 1, "The public key is missing!")

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            state, message = self.user_checker(user_info, args["key"])
            if state:
                self.logger.info("User public key uploaded!")
                return AMApiBase.embed_data({}, 0, "User public key uploaded!")
            else:
                return AMApiBase.embed_data({}, 1, "Internal error: {0}".format(message))
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def delete(self):
        self.logger.info("Received a remove key request!")
        args = self.parse_args()

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            state, message = self.user_checker(user_info, "")
            if state:
                self.logger.info("User public key removed!")
                return AMApiBase.embed_data({}, 0, "User public key removed!")
            else:
                return AMApiBase.embed_data({}, 1, "Internal error: {0}".format(message))
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def user_checker(self, user_info, key):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_user_roles(user_info["id"])
                self.logger.debug("Check the chroot role, when setting a user public key!")
                for role in roles:
                    self.logger.debug("Role name: {0}".format(role))
                    if self.db.is_chroot_role(role):
                        self.logger.debug("Found a chroot role attached to the {0} user!".format(user_info["name"]))
                        self.key_handler(user_info["name"], "Chroot", 'cloud.chroot', key)

                    if role == "linux_user":
                        self.logger.debug("Found a Linux user role attached to the {0} user!".format(user_info["name"]))
                        self.key_handler(user_info["name"], "Linux", 'cloud.linuxuser', key)
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, ex
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, ""
        else:
            return False, message_open

    def key_handler(self, username, user_type, list_name, key):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        if user_list:
            self.logger.debug("The {0} user list exists!".format(user_type))
            for val in user_list:
                if val["name"] == username:
                    val["public_key"] = key
                    break
            self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
            cmc.set_property(list_name, json.dumps(user_list))
