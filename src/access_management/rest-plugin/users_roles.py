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
from cmframework.apis import cmclient


class UsersRoles(AMApiBase):

    """
    User add role operations

    .. :quickref: User roles;User add role operations

    .. http:post:: /am/v1/users/roles

    **Start User add role**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users/roles HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
            "role_name": test_role
        }

    :> json string user: The user's id or name.
    :> json string role_name: The user's new role.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role add to user."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    User remove role operations

    .. :quickref: User roles;User remove role operations

    .. http:delete:: /am/v1/users/roles

    **Start User remove role**

    **Example request**:

    .. sourcecode:: http

        DELETE am/v1/users/roles HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
            "role_name": test_role
        }

    :> json string user: The user's id or name.
    :> json string role_name: Remove this role from the user.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role removed from user."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users/roles']
    parser_arguments = ['user',
                        'role_name']

    def post(self):
        self.logger.info("Received a user add role request!")
        args = self.parse_args()

        if args["role_name"] is None:
            self.logger.error("Role name parameter is missing!")
            return AMApiBase.embed_data({}, 1, "Role name parameter is missing!")

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            username, def_project = self.get_user_from_uuid(user_info["id"])
            state, message = self._add_role(args['role_name'], def_project, user_info)

            if state:
                self.logger.info("The {0} role is added to the {1} user!".format(args["role_name"], user_info["name"]))
                return AMApiBase.embed_data({}, 0, "Role add to user.")
            else:
                self.logger.error("The {0} role addition to the {1} user failed: {2}".format(args["role_name"], user_info["name"], message))
                return AMApiBase.construct_error_response(1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def delete(self):
        self.logger.info("Received a user remove role request!")
        args = self.parse_args()

        if args["role_name"] is None:
            self.logger.error("Role name parameter is missing!")
            return AMApiBase.embed_data({}, 1, "Role name parameter is missing!")

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            token_owner = self.get_uuid_from_token()
            if user_info["id"] == token_owner and args["role_name"] == defaults.INF_ADMIN_ROLE_NAME:
                self.logger.error("The {0} user tried to removed own ".format(user_info["name"])+defaults.INF_ADMIN_ROLE_NAME+" role!")
                return AMApiBase.embed_data({}, 1, "You cannot remove own "+defaults.INF_ADMIN_ROLE_NAME+" role!")

            username, def_project = self.get_user_from_uuid(user_info["id"])
            state, message = self._remove_role(args["role_name"], def_project, user_info)

            if state:
                self.logger.info("The {0} role removed from the {1} user!".format(args["role_name"], user_info["name"]))
                return AMApiBase.embed_data({}, 0, "Role removed from user.")
            else:
                self.logger.error("Removal of {0} role from {1} user failed: {2}".format(args["role_name"], user_info["name"], message))
                return AMApiBase.construct_error_response(1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def _remove_role(self, role_name, project, user_info):
        state_open, message_open = self._open_db()
        if state_open:
            need_admin_role = True
            try:
                roles = self.db.get_user_roles(user_info["id"])
            except NotExist:
                return False, 'User {0} does not exist.'.format(user_info["name"])
            except Exception as ex:
                return False, 'Error retrieving roles for user {0}: {1}'.format(user_info["name"], ex)
            if (role_name == defaults.INF_ADMIN_ROLE_NAME and defaults.OS_ADMIN_ROLE_NAME in roles) or (role_name == defaults.OS_ADMIN_ROLE_NAME and defaults.INF_ADMIN_ROLE_NAME in roles):
                need_admin_role = False
            state, message = self.modify_role_in_keystone(role_name, user_info["id"], "delete", project, need_admin_role)
            if not state:
                return state, message

            try:
#            self.db.connect()
            # remove chroot user only if the role is chroot role
                self.logger.debug("Check the chroot role, when removing a role!")
                if self.db.is_chroot_role(role_name):
                    self.logger.debug("This is a chroot role!")
                    for x in range(3):
                        self.remove_chroot_linux_role_handling(user_info["name"], "Chroot", "cloud.chroot")
                        time.sleep(2)
                        if self.check_chroot_linux_state(user_info["name"], "cloud.chroot", "absent"):
                            self.db.delete_user_role(user_info["id"], role_name)
                            return True, "Success"

                    self.logger.error("The {0} user cannot remove {1} role, because the cm framework set_property's function failed.".format(user_info["name"], role_name))
                    return False, "The chroot user is not removed. Please try again!"

                if role_name == "linux_user":
                    self.logger.debug("This is a linux_user role!")
                    for x in range(3):
                        self.remove_chroot_linux_role_handling(user_info["name"], "Linux", "cloud.linuxuser")
                        time.sleep(2)
                        if self.check_chroot_linux_state(user_info["name"], "cloud.linuxuser", "absent"):
                            self.db.delete_user_role(user_info["id"], role_name)
                            return True, "Success"

                    self.logger.error("The {0} user cannot remove {1} role, because the cm framework set_property's function failed.".format(user_info["name"], role_name))
                    return False, "The linux user is not removed. Please try again!"

                self.db.delete_user_role(user_info["id"], role_name)
            except amdb.NotAllowedOperation:
                return False, 'Service role cannot be deleted: {0}'.format(user_info["name"])
            except amdb.NotExist:
                return False, 'User {0} has no role {1}.'.format(user_info["name"], role_name)
            except amdb.AlreadyExist:
                return False, 'Role for user already exists in table: {0}:{1}'.format(user_info["name"], role_name)
            except Exception as ex:
                return False, ex
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, "Success"
        else:
            return False, message_open

    def _add_role(self, role_name, project, user_info):
        state, message = self.modify_role_in_keystone(role_name, user_info["id"], "put", project)
        if not state:
            return state, message

        state, message = self.add_role_db_functions(role_name, user_info)
        return state, message

    def add_role_db_functions(self, role_name, user_info):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_user_roles(user_info["id"])
                self.db.add_user_role(user_info["id"], role_name)

                # create chroot user only if the role is chroot role
                self.logger.debug("Check the chroot role, when adding a role!")
                if self.db.is_chroot_role(role_name):
                    self.logger.debug("This is a chroot role!")

                    if "linux_user" in roles:
                        self.logger.error("The {0} user cannot get {1} chroot role, because this user has a linux_user role".format(user_info["name"], role_name))
                        self.db.delete_user_role(user_info["id"], role_name)
                        return False, "The {0} user cannot get {1} chroot role, because this user has a linux_user role".format(user_info["name"], role_name)

                    for x in range(3):
                        self.add_chroot_linux_role_handling(user_info["id"], "Chroot", "cloud.chroot", role_name)
                        time.sleep(2)
                        if self.check_chroot_linux_state(user_info["name"], "cloud.chroot", "present"):
                            return True, "Success"

                    self.db.delete_user_role(user_info["id"], role_name)
                    self.logger.error("The {0} user cannot get {1} role, because the cm framework set_property's function failed.".format(user_info["name"], role_name))
                    return False, "The chroot user is not created. Please try again!"

                # create linux user only if the role is linux_user role
                if role_name == "linux_user":
                    self.logger.debug("This is a linux_user role!")
                    have_a_chroot = False
                    self.logger.debug("role list: {0}".format(roles))
                    for role in roles:
                        if self.db.is_chroot_role(role):
                            have_a_chroot = True

                    if have_a_chroot:
                        self.logger.error("The {0} user cannot get {1} role, because this user has a chroot role".format(user_info["name"], role_name))
                        self.db.delete_user_role(user_info["id"], role_name)
                        return False, "The {0} user cannot get {1} role, because this user has a chroot role".format(user_info["name"], role_name)

                    for x in range(3):
                        self.add_chroot_linux_role_handling(user_info["id"], "Linux", "cloud.linuxuser", None)
                        time.sleep(2)
                        if self.check_chroot_linux_state(user_info["name"], "cloud.linuxuser", "present"):
                            return True, "Success"

                    self.db.delete_user_role(user_info["id"], role_name)
                    self.logger.error("The {0} user cannot get {1} role, because the cm framework set_property's function failed.".format(user_info["name"], role_name))
                    return False, "The linux user is not created. Please try again!"

            except amdb.NotExist:
                return False, 'The user {} or role {} not exist.'.format(user_info["name"], role_name)
            except amdb.AlreadyExist:
                return False, 'Role for user already exists in table: {0}:{1}'.format(user_info["name"], role_name)
            except Exception as ex:
                return False, ex
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, "Success"
        else:
            return False, message_open

    def add_chroot_linux_role_handling(self, user_id, user_type, list_name, group):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        if user_list is None:
            cmc.set_property(list_name, json.dumps([]))
            user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        add = True
        self.logger.debug("The {0} user list exists!".format(user_type))
        username, def_project = self.get_user_from_uuid(user_id)
        self.logger.debug("Username: {0}".format(username))
        for element in user_list:
            if element["name"] == username:
                if element["state"] == "present":
                    self.logger.error("The {0} user has an active {1} chroot role".format(username, element["group"]))
                    self.db.delete_user_role(user_id, group)
                    return False, "The {0} users have an active {1} chroot role".format(username, element["group"])
                else:
                    self.logger.debug("The {0} user has an active linux_user role".format(username))
                    if group is not None:
                        element["group"] = group
                    element["state"] = "present"
                    element["remove"] = "no"
                    add = False
        if add:
            new_user = {"name": username, "password": "", "state": "present", "remove": "no", "lock_state": "-u", "public_key": ""}
            if group is not None:
                new_user["group"]= group
            user_list.append(new_user)
        self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
        cmc.set_property(list_name, json.dumps(user_list))

    def remove_chroot_linux_role_handling(self, username, user_type, list_name):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("{0} user list before the change: {1}".format(user_type, json.dumps(user_list)))
        if user_list is not None:
            self.logger.debug("The {0} user list exists!".format(user_type))
            for val in user_list:
                if val["name"] == username:
                    val["public_key"] = ""
                    val["state"] = "absent"
                    val["remove"] = "yes"
                    val["password"] = ""
                    break
            self.logger.debug("{0} user list after the change: {1}".format(user_type, json.dumps(user_list)))
            cmc.set_property(list_name, json.dumps(user_list))
