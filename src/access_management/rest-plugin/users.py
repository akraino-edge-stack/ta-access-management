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

import time
import access_management.db.amdb as amdb
from am_api_base import *
from keystoneauth1 import exceptions
from cmframework.apis import cmclient


class Users(AMApiBase):

    """
    User create operations

    .. :quickref: Users;User create operations

    .. http:post:: /am/v1/users

    **Start User create**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "username": "user_1",
            "password": "Passwd_1",
            "email": "test@mail.com",
            "project": "10f8fa2c6efe409d8207517128f03265",
            "description": "desc"
        }

    :> json string username: The created user name.
    :> json string password: The user's password.
    :> json string email: The user's e-mail.
    :> json string project: ID of the project to be set as primary project for the user.
    :> json string description: The user's description.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "",
            "data":
            {
                "id": <uuid>
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: a dictionary with the created user's id
    :> json string id: The created user's id.

    Users list operations

    .. :quickref: Users;Users list operations

    .. http:get:: /am/v1/users

    **Start Users list**

    **Example request**:

    .. sourcecode:: http

        GET am/v1/users HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "",
            "data":
            {
                "0edf341a27544c349b7c37bb76ab25d1":
                {
                    "enabled": true,
                    "id": "0edf341a27544c349b7c37bb76ab25d1",
                    "name": "cinder",
                    "password_expires_at": null
                },
                "32e8859519f94b1ea80f61d53d17e74e":
                {
                    "enabled": true,
                    "id": "32e8859519f94b1ea80f61d53d17e74e",
                    "name": "nova",
                    "password_expires_at": null
                }
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: The existing users.
    :> json string enabled: The user's state.
    :> json string id: The user's id.
    :> json string name: The user's name.
    :> json string password_expires_at: The user's password expiration date.

    User delete operations

    .. :quickref: Users;User delete operations

    .. http:delete:: /am/v1/users

    **Start User delete**

    **Example request**:

    .. sourcecode:: http

        DELETE am/v1/users HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
        }

    :> json string user: The removed user's id or user name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User deleted!"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users']
    parser_arguments = ['username',
                        'password',
                        'email',
                        'user',
                        'project',
                        'description']

    def post(self):
        self.logger.info("Received a user create request!")
        args = self.parse_args()

        if args["email"] is not None:
            if re.match("^[\.a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+\.[a-z]+$", args["email"]) is None:
                self.logger.error("E-mail validation failed!")
                return AMApiBase.embed_data({}, 1, "E-mail validation failed!")

        if self.id_validator(args["username"]):
            self.logger.error("{0} username is invalid, because cannot assign a valid uuid to it.".format(args["username"]))
            return AMApiBase.embed_data({}, 1, "{0} username is invalid, because cannot assign a valid uuid to it.".format(args["username"]))

        if args["project"]:
            projectidstate = self.id_validator(args["project"])
            if projectidstate == False:
                self.logger.error("Project id validation failed")
                return AMApiBase.embed_data({}, 1, "Project id validation failed")

        if re.match("^[a-zA-Z0-9_-]+$", args["username"]) is None:
            self.logger.error("Username validation failed!")
            return AMApiBase.embed_data({}, 1, "Username validation failed!")

        passstate = self.passwd_validator(args["password"])
        if passstate is not None:
            self.logger.error(passstate)
            return AMApiBase.embed_data({}, 1, passstate)

        state, result = self._create_user(args)
        if state:
            self.logger.info("User created!")
            return AMApiBase.embed_data({"id": result}, 0, "")
        else:
            return AMApiBase.embed_data({}, 1, result)

    def get(self):
        self.logger.info("Received a user list request!")
        user_list = {}
        try:
            self.keystone = self.auth_keystone()
            u_list = self.keystone.users.list()
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)

        for element in u_list:
            user_list.update({element.id : element._info})

        self.logger.info("The user list response done!")
        return AMApiBase.embed_data(user_list, 0, "User list.")

    def delete(self):
        self.logger.info("Received a user delete request!")
        args = self.parse_args()

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            token_owner = self.get_uuid_from_token()
            if user_info["id"] == token_owner:
                self.logger.error("The {0} user tried to delete own account!".format(user_info["id"]))
                return AMApiBase.embed_data({}, 1, "You cannot delete your own account!")

            state, message = self._delete_user(user_info)

            if state:
                self.logger.info("User deleted!")
                return AMApiBase.embed_data({}, 0, "User deleted!")
            else:
                self.logger.error(message)
                return AMApiBase.embed_data({}, 1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def _delete_user(self, user_info):
        state, name = self._delete_user_from_db(user_info)
        if state:
            self.logger.info("User removed from the db!")
            try:
                self.keystone.users.delete(user_info["id"])
            except exceptions.http.NotFound as ex:
                self.logger.info("{0} user does not exist in the keystone!".format(user_info["name"]))
                return True, "Done, but this user didn't exist in the keystone!"
            except Exception as ex:
                self.logger.error("{0}".format(ex))
                return False, "{0}".format(ex)
            return True, "Done"
        else:
            return False, name

    def _delete_user_from_db(self, user_info):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_user_roles(user_info["id"])

                for role in roles:
                    if self.db.is_chroot_role(role):
                        self.logger.debug("This user has a chroot role.")
                        for x in range(3):
                            self.remove_chroot_linux_role_handling(user_info["id"], "Chroot", "cloud.chroot")
                            time.sleep(2)
                            if self.check_chroot_linux_state(user_info["name"], "cloud.chroot", "absent"):
                                self.db.delete_user(user_info["id"])
                                return True, user_info["name"]

                    if role == "linux_user":
                        self.logger.debug("This user has a linux_user role!")
                        for x in range(3):
                            self.remove_chroot_linux_role_handling(user_info["id"], "Linux", "cloud.linuxuser")
                            time.sleep(2)
                            if self.check_chroot_linux_state(user_info["name"], "cloud.linuxuser", "absent"):
                                self.db.delete_user(user_info["id"])
                                return True, user_info["name"]

                self.db.delete_user(user_info["id"])
            except amdb.NotAllowedOperation:
                self.logger.error("Deleting service user is not allowed: {0}".format(user_info["name"]))
                return False, "Deleting service user is not allowed: {0}".format(user_info["name"])
            except amdb.NotExist:
                self.logger.info("The {0} user does not exist!".format(user_info["name"]))
                return True, ""
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, user_info["name"]
        else:
            return False, message_open

    def _create_user(self, args):
        roles = []
        ks_member_roleid = self.get_role_id(defaults.KS_MEMBER_NAME)
        if ks_member_roleid is None:
            self.logger.error("Member user role not found!")
            return False, "Member user role not found!"
        else:
            roles.append(ks_member_roleid)
        basic_member_roleid = self.get_role_id(defaults.AM_MEMBER_NAME)
        if basic_member_roleid is None:
            self.logger.error("basic_member user role not found!")
            return False, "basic_member user role not found!"
        else:
            roles.append(basic_member_roleid)

        um_proj_id = self.get_project_id(defaults.PROJECT_NAME)
        if um_proj_id is None:
            self.logger.error("The user management project is not found!")
            return False, "The user management project is not found!"

        if args["email"] is None:
            args["email"] = 'None'
        if args["project"] is None:
            args["project"] = um_proj_id

        try:
            c_user_out = self.keystone.users.create(name=args["username"], password=args["password"], email=args["email"], default_project=args["project"],  description=args["description"])
        except exceptions.http.Conflict as ex:
            self.logger.error("{0}".format(ex))
            return False, "This user exists in the keystone!"
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)

        ID = c_user_out.id
        state, message = self._add_basic_roles(um_proj_id, ID, roles)
        if not state:
            return False, message
        if args["project"] != um_proj_id:
            state, message = self._add_basic_roles(args["project"], ID, [ks_member_roleid])
            if not state:
                return False, message
        return self._create_user_in_db(ID, args)

    def _add_basic_roles(self, project, ID, roles):
        for role in roles:
            try:
                self.keystone.roles.grant(role, user=ID, project=project)
            except Exception:
                try:
                    self.keystone.roles.grant(role, user=ID, project=project)
                except Exception as ex:
                    self.logger.error("{0}".format(ex))
                    self.keystone.users.delete(ID)
                    return False, "{0}".format(ex)
        return True, "OK"

    def _create_user_in_db(self, ID, args):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                self.db.create_user(ID, args["username"])
                self.db.add_user_role(ID, defaults.AM_MEMBER_NAME)
            except amdb.AlreadyExist as ex1:
                self.logger.error("User already exists in table!")
                try:
                    self.keystone.users.delete(ID)
                    self.db.delete_user(ID)
                except amdb.NotAllowedOperation as ex2:
                    self.logger.error("Internal error: Except1: {0}, Except2: {1}".format(ex1, ex2))
                    return False, "Except1: {0}, Except2: {1}".format(ex1, ex2)
                except Exception as ex3:
                    self.logger.error("Internal error: Except1: {0}, Except2: {1}".format(ex1, ex3))
                    return False, "Except1: {0}, Except2: {1}".format(ex1, ex3)
                return False, "User already exists!"
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                try:
                    self.keystone.users.delete(ID)
                except exceptions.http.NotFound as ex:
                    self.logger.error("{0}".format(ex))
                    return False, "This user does not exist in the keystone!"
                except Exception as ex:
                    self.logger.error("{0}".format(ex))
                    return False, "{0}".format(ex)
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, ID
        else:
            return False, message_open

    def remove_chroot_linux_role_handling(self, user_id, user_type, list_name):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        if user_list is not None:
            self.logger.debug("The {0} user list exists!".format(user_type))
            username, def_project = self.get_user_from_uuid(user_id)
            self.logger.debug("User name: {0}".format(username))
            for val in user_list:
                if val["name"] == username:
                    val["public_key"] = ""
                    val["state"] = "absent"
                    val["remove"] = "yes"
                    val["password"] = ""
                    break
            self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
            cmc.set_property(list_name, json.dumps(user_list))
