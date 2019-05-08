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
import requests
import access_management.db.amdb as amdb
from am_api_base import *
from keystoneauth1 import exceptions
from cmframework.apis import cmclient


class UsersOwnpasswords(AMApiBase):

    """
    User set password operations

    .. :quickref: User ownpasswords;User set password operations

    .. http:post:: /am/v1/users/ownpasswords

    **Start User set password**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users/ownpasswords HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "npassword: "Passwd_1",
            "opassword: "Passwd_2",
            "username": "test_user"
        }

    :> json string npassword: The user's new password
    :> json string opassword: The user's old password
    :> json string username: The user's username
    :> json string id: The user's ID
    Only one of username or id needs to be present.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User password changed successfully!"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users/ownpasswords']
    parser_arguments = ['npassword',
                        'opassword',
                        'username',
                        'id']
    FAILURE_RESPONSE = AMApiBase.embed_data({}, 1, "Password change failed!")

    def post(self):
        self.logger.info("Received a set password request!")
        args = self.parse_args()

        user = {}
        state_open, message_open = self._open_db()
        if state_open:
            try:
                if args["username"]:
                    user["name"] = args["username"]
                    user["uuid"] = self.db.get_user_uuid(args["username"])
                else:
                    user["uuid"] = args["id"]
                    user["name"] = self.db.get_user_name(args["id"])

                try:
                    keystone = self.auth_keystone_with_pass(args["opassword"], user["name"])
                    passstate = self.passwd_validator(args["npassword"])
                    if passstate is not None:
                        self.logger.error(passstate)
                        return AMApiBase.embed_data({}, 1, passstate)
                    keystone.users.update_password(args["opassword"], args["npassword"])
                    state = True
                except exceptions.http.Unauthorized as ex:
                    if "password is expired" in ex.message:
                        passstate = self.passwd_validator(args["npassword"])
                        if passstate is not None:
                            self.logger.error(passstate)
                            return AMApiBase.embed_data({}, 1, passstate)
                        state = self.change_password_with_request(args, user["uuid"])
                    else:
                        self.logger.error("{0}".format(ex))
                        state = False
                except Exception as ex:
                    self.logger.error("{0}".format(ex))
                    return self.FAILURE_RESPONSE

                if state:
                    state = self.set_ownpass_in_db(args, user)
                    if state:
                        self.logger.info("User password changed successfully!")
                        return AMApiBase.embed_data({}, 0, "User password changed successfully!")
                    else:
                        return self.FAILURE_RESPONSE
                else:
                    return self.FAILURE_RESPONSE

            except amdb.NotExist as ex:
                self.logger.error("User does not exist")
                return self.FAILURE_RESPONSE
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return self.FAILURE_RESPONSE
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
        else:
            return self.FAILURE_RESPONSE

    def change_password_with_request(self, args, uuid):
        url = self.config["Keystone"]["auth_uri"] + "/users/" + uuid + "/password"
        parameter = {"user": {"password": args["npassword"], "original_password": args["opassword"]}}
        header = {"Content-Type": "application/json"}
        s_user_out = requests.post(url, data=json.dumps(parameter), headers=header, timeout=30)

        if s_user_out.status_code != 204:
            s_user_out = s_user_out.json()
            self.logger.error(s_user_out["error"]["message"])
            return False
        return True

    def set_ownpass_in_db(self, args, user):
        linux_user_role = False
        chroot_user_role = False
        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_user_roles(user["uuid"])

                for role in roles:
                    if self.db.is_chroot_role(role):
                        chroot_user_role = True
                    if role == "linux_user":
                        linux_user_role = True

                # if the user has a chroot or linux account, change the pwd of that also
                if chroot_user_role:
                    self.linux_chroot_pass_handling("Chroot", "cloud.chroot", args["npassword"], user["name"])
                if linux_user_role:
                    self.linux_chroot_pass_handling("Linux", "cloud.linuxuser", args["npassword"], user["name"])

            except amdb.NotExist as ex:
                self.logger.error("User does not exist")
                return False
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
        else:
            self.logger.error("Could not open DB")
            return False

        return True

    def linux_chroot_pass_handling(self, user_type, list_name, passwd, username):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        if user_list is not None:
            self.logger.debug("The {0} user list exists!".format(user_type))
            self.logger.debug("Username: {0}".format(username))
            for val in user_list:
                if val["name"] == username:
                    val["password"] = crypt.crypt(passwd, crypt.mksalt(crypt.METHOD_SHA512))
                    break
            self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
            cmc.set_property(list_name, json.dumps(user_list))
