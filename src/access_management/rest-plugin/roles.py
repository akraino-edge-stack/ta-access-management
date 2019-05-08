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


class Roles(AMApiBase):

    """
    Role create operations

    .. :quickref: Roles;Role create operations

    .. http:post:: /am/v1/roles

    **Start Role create**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/roles HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
            "desc": "This is a test role"
        }

    :> json string role_name: The created role name.
    :> json string desc: A short description from the created role.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role created."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    Role modify operations

    .. :quickref: Roles;Role modify operations

    .. http:put:: /am/v1/roles

    **Start Role modify**

    **Example request**:

    .. sourcecode:: http

        PUT am/v1/roles HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
            "desc": "This is a test role"
        }

    :> json string role_name: The modified role name.
    :> json string desc: A short description from the modified role.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role modified."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    Role delete operations

    .. :quickref: Roles;Role delete operations

    .. http:delete:: /am/v1/roles

    **Start Role delete**

    **Example request**:

    .. sourcecode:: http

        DELETE am/v1/roles HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
        }

    :> json string role_name: The deleted role name.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role deleted."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    Role list operations

    .. :quickref: Roles;Role list operations

    .. http:get:: /am/v1/roles

    **Start Role list**

    **Example request**:

    .. sourcecode:: http

        GET am/v1/roles HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Role list."
            "data":
            {
                "alarm_admin":
                {
                    "desc": "Alarm Administrator",
                    "is_chroot": false,
                    "is_service": true,
                    "role_name": "alarm_admin"
                },
                "alarm_viewer":
                {
                    "desc": "Alarm Viewer",
                    "is_chroot": false,
                    "is_service": true,
                    "role_name": "alarm_viewer"
                }
            }
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    :> json object data: a dictionary with the existing roles
    :> json string role_name: The role name.
    :> json string desc: The role description.
    :> json string is_chroot: If this field is true, then this is a chroot user role.
    :> json string is_service: If this field is true, then this is a service role and we created this role in deploymnet time.
    """

    endpoints = ['roles']
    parser_arguments = ['role_name',
                        'desc']

    def post(self):
        self.logger.info("Received a role create request!")
        args = self.parse_args()
        if args["desc"] is None:
            args["desc"] = ""
        state, result = self._role_create(args)

        if state:
            self.logger.info("The {0} role created!".format(args["role_name"]))
            return AMApiBase.embed_data({}, 0, result)
        else:
            self.logger.error("The {0} role creation failed: {1}".format(args["role_name"], result))
            return AMApiBase.construct_error_response(1, result)

    def put(self):
        self.logger.info("Received a role modify request!")
        args = self.parse_args()
        if args["desc"] is None:
            args["desc"] = ""
        state, result = self._role_modify(args)

        if state:
            self.logger.info("The {0} role modified!".format(args["role_name"]))
            return AMApiBase.embed_data({}, 0, result)
        else:
            self.logger.error("The {0} role modify failed: {1}".format(args["role_name"], result))
            return AMApiBase.construct_error_response(1, result)

    def get(self):
        self.logger.info("Received a role list request!")
        state, roles = self._role_list()

        if state:
            self.logger.info("The role list response done!")
            return AMApiBase.embed_data(roles, 0, "Role list.")
        else:
            self.logger.error("Role list creation failed: {0}".format(roles))
            return AMApiBase.construct_error_response(1, roles)

    def delete(self):
        self.logger.info("Received a role delete request!")
        args = self.parse_args()

        state, message = self._role_delete(args)

        if state:
            self.logger.info("The {0} role deleted!".format(args["role_name"]))
            return AMApiBase.embed_data({}, 0, message)
        else:
            self.logger.error("The {0} role deletion failed: {1}".format(args["role_name"], message))
            return AMApiBase.construct_error_response(1, message)

    def _role_modify(self, args):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                self.db.set_role_param(args["role_name"], args["desc"])
            except amdb.NotAllowedOperation:
                self.logger.error("Modifying service role is not allowed: {0}".format(args["role_name"]))
                return False, "Modifying service role is not allowed: {0}".format(args["role_name"])
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, "Role modified."
        else:
            return False, message_open

    def _role_create(self, args):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                self.db.create_role(args["role_name"], args["desc"])
                try:
                    self.keystone.roles.create(args["role_name"])
                except Exception as ex:
                    self.db.delete_role(args["role_name"])
                    self.logger.error("Role {} already exists".format(args["role_name"]))
                    return False, "Role {} already exists".format(args["role_name"])
            except amdb.AlreadyExist:
                self.logger.error("Role already exists in table: {0}".format(args["role_name"]))
                return False, "Role already exists in table: {0}".format(args["role_name"])
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
        else:
            return False, message_open
        return True, "Role created."

    def _role_list(self):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                roles = self.db.get_all_roles()
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, roles
        else:
            return False, message_open

    def _add_roles_back_to_users(self, role_name):
        uuid_list = self.db.get_role_users(role_name)
        for uuid in uuid_list:
            username, def_project = self.get_user_from_uuid(uuid)
            state, message = self.modify_role_in_keystone(role_name, uuid, "put", def_project)
            if not state:
                return False, "Role deletion failed, please try again!"
        return False, "Role deletion failed, try again"

    def _role_delete(self, args):
        state_open, message_open = self._open_db()
        if state_open:
            try:
                db_role = self.db.get_role(args["role_name"])
                if not db_role._data["is_service"]:
                    role_id = self.get_role_id(args["role_name"])
                    if role_id is not None:
                        try:
                            self.keystone.roles.delete(role_id)
                        except Exception as ex:
                            self.logger.error("Some problem occured: {}".format(ex))
                            return False, "Some problem occured: {}".format(ex)

                        try:
                            self.db.delete_role(args["role_name"])
                        except Exception:
                            try:
                                self.keystone.roles.create(args["role_name"])
                            except Exception:
                                self.logger.error("Error during deleting role: {}".format(args["role_name"]))
                                return False, "Error during deleting role: {}".format(args["role_name"])
                            state, message = self._add_roles_back_to_users(args["role_name"])
                            return state, message
                else:
                    raise amdb.NotAllowedOperation("")
            except amdb.NotAllowedOperation:
                self.logger.error("Deleting service role is not allowed: {0}".format(args["role_name"]))
                return False, "Deleting service role is not allowed: {0}".format(args["role_name"])
            except Exception as ex:
                self.logger.error("Internal error: {0}".format(ex))
                return False, "Internal error: {0}".format(ex)
            finally:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
            return True, "Role deleted."
        else:
            return False, message_open
