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
import crypt
import time
from am_api_base import *
from keystoneauth1 import exceptions
from cmframework.apis import cmclient


class UsersPasswords(AMApiBase):

    """
    User reset password operations

    .. :quickref: User passwords;User reset password operations

    .. http:post:: /am/v1/users/passwords

    **Start User reset password**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users/passwords HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
            "npassword: "Passwd_1"
        }

    :> json string user: The user's id or name.
    :> json string npassword: The user's new password

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Users password reset success."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users/passwords']
    parser_arguments = ['user',
                        'npassword']

    def post(self):
        self.logger.info("Received a reset password request!")
        args = self.parse_args()

        passstate = self.passwd_validator(args["npassword"])
        if passstate is not None:
            self.logger.error(passstate)
            return AMApiBase.embed_data({}, 1, passstate)

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            status, message = self._reset_pass(user_info, args['npassword'])

            if status:
                self.logger.info("Password reset successfully!")
                return AMApiBase.embed_data({}, 0, "Password reset successfully!")
            else:
                self.logger.error("Internal error: {0}".format(message))
                return AMApiBase.embed_data({}, 1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def _reset_pass(self, user_info, passwd):
        try:
            reset = self.keystone.users.update(user_info["id"], password=passwd)
        except exceptions.http.NotFound as ex:
            self.logger.error("{0}".format(ex))
            return False, "This user does not exist in the keystone!"
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)

        self.logger.info(reset)
        passwd_hash = crypt.crypt(passwd, crypt.mksalt(crypt.METHOD_SHA512))

        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_user_roles(user_info["id"])
                for role in roles:
                    if self.db.is_chroot_role(role):
                        # if the user has a chroot account, change the pwd of that also
                        for x in range(3):
                            self.linux_chroot_pass_handling(user_info["name"], "Chroot", "cloud.chroot", passwd_hash)
                            time.sleep(5)
                            if self.check_chroot_linux_pass_state(user_info["name"], "cloud.chroot", passwd_hash):
                                return True, "Success"
                        return False, "The user handler is busy, please try again."
                    if role == "linux_user":
                        # if the user has a Linux user account, change the pwd of that also
                        for x in range(3):
                            self.linux_chroot_pass_handling(user_info["name"], "Linux", "cloud.linuxuser", passwd_hash)
                            time.sleep(5)
                            if self.check_chroot_linux_pass_state(user_info["name"], "cloud.linuxuser", passwd_hash):
                                return True, "Success"
                        return False, "The user handler is busy, please try again."
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return AMApiBase.embed_data({}, 1, "Internal error: {0}".format(ex))
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, reset
        else:
            return False, message_open

    def linux_chroot_pass_handling(self, username, user_type, list_name, passwd):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        if user_list is not None:
            self.logger.debug("The {0} user list exist!".format(user_type))
            for val in user_list:
                if val["name"] == username:
                    val["password"] = passwd
                    break
            self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
            cmc.set_property(list_name, json.dumps(user_list))

    def check_chroot_linux_pass_state(self, username, list_name, password):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("Start the user list check")
        for val in user_list:
            if val["name"] == username and val["password"] == password:
                self.logger.debug("{0} user's password changed!".format(username))
                return True
        self.logger.debug("{0} user's password is not changed!".format(username))
        return False
