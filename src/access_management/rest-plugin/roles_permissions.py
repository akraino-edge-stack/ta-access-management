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
import access_management.db.amdb as amdb


class RolesPermissions(AMApiBase):

    """
    Role add permission operations

    .. :quickref: Roles permission;Role add permission operations

    .. http:post:: /am/v1/roles/permissions

    **Start Role add permission**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/roles/permissions HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
            "res_path": "domain/domain_object"
            "res_op": "GET"
        }

    :> json string role_name: The role the permission gets to be added to.
    :> json string res_path: The endpoint of the permission to be added.
    :> json string res_op: The method of the permission to be added.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Resource added to role"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero

    Role remove permission operations

    .. :quickref: Roles permission;Role remove permission operations

    .. http:delete:: /am/v1/roles/permissions

    **Start Role remove permission**

    **Example request**:

    .. sourcecode:: http

        DELETE am/v1/roles/permissions HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "role_name": "test_role"
            "res_path": "domain/domain_object"
            "res_op": "GET"
        }

    :> json string role_name: The role the permission gets to be removed from.
    :> json string res_path: The endpoint of the permission to be removed.
    :> json string res_op: The method of the permission to be removed.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "Resource removed from role"
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['roles/permissions']
    parser_arguments = ['role_name',
                        'res_path',
                        'res_op']

    def post(self):
        self.logger.info("Received a role add permission request!")
        args = self.parse_args()

        state, permissions = self._add_permission(args)

        if state:
            self.logger.info("The {1}:{2} permission added to {0} role!".format(args["role_name"], args["res_path"], args["res_op"]))
            return AMApiBase.embed_data({}, 0, permissions)
        else:
            self.logger.error("The request to add permission {1}:{2} to role {0} failed: {3}".format(args["role_name"], args["res_path"], args["res_op"], permissions))
            return AMApiBase.embed_data({}, 1, permissions)

    def delete(self):
        self.logger.info("Received a role remove permission request!")
        args = self.parse_args()

        state, result = self._remove_permission(args)

        if state:
            self.logger.info("The {1}:{2} permission removed from {0} role!".format(args["role_name"], args["res_path"], args["res_op"]))
            return AMApiBase.embed_data({}, 0, result)
        else:
            self.logger.error("The request to remove permission {1}:{2} from role {0} failed: {3}".format(args["role_name"], args["res_path"], args["res_op"], result))
            return AMApiBase.construct_error_response(1, result)

    def _remove_permission(self, args):
        state_open, message_open = self._open_db()
        if state_open:
            state_remove, message_remove = self._delete_role_resource(args)
            if state_remove:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
                return True, state_remove
            else:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
                return False, state_remove
        else:
            return False, message_open

    def _add_permission(self, args):
        state_open, message_open = self._open_db()
        if state_open:
            state_add, message_add = self._add_resource_to_role(args)
            if state_add:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
                return True, message_add
            else:
                state_close, message_close = self._close_db()
                if not state_close:
                    self._close_db()
                return False, message_add
        else:
            return False, message_open

    def _add_resource_to_role(self, args):
        try:
            self.db.add_resource_to_role(args["role_name"], args["res_path"], args["res_op"])
        except amdb.AlreadyExist:
            message = "Role-permission pair already exists in table: {0}:{1}, {2}".format(args["role_name"],args["res_path"],args["res_op"])
            self.logger.error(message)
            return False, message
        except amdb.NotAllowedOperation:
            message = "Service role cannot be modified: {0}".format(args["role_name"])
            self.logger.error(message)
            return False, message
        except Exception as ex:
            message = "Internal error: {0}".format(ex)
            self.logger.error(message)
            return False, message
        return True, "Permission added to role!"

    def _delete_role_resource(self, args):
        try:
            self.db.delete_role_resource(args["role_name"],args["res_path"],args["res_op"])
        except amdb.NotExist:
            message = "Role {0} has no such resource:operation: {1}:{2}".format(args["role_name"],args["res_path"],args["res_op"])
            self.logger.error(message)
            return False, message
        except amdb.NotAllowedOperation:
            message = "Service role cannot be modified: {0}".format(args["role_name"])
            self.logger.error(message)
            return False, message
        except Exception as ex:
            message = "Internal error: {0}".format(ex)
            self.logger.error(message)
            return False, message
        return True, "Permission removed from role!"
