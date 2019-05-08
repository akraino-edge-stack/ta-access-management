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
from keystoneauth1 import exceptions

class UsersParameters(AMApiBase):

    """
    User set parameter operations

    .. :quickref: User set parameter;User set parameter operations

    .. http:post:: /am/v1/users/parameters

    **Start User set parameter**

    **Example request**:

    .. sourcecode:: http

        POST am/v1/users/parameters HTTP/1.1
        Host: haproxyvip:61200
        Accept: application/json
        {
            "user": <uuid> or <username>
            "project_id: <project_id>
            "email": <email>
        }

    :> json string user: The user's id or name.
    :> json string project_id: The user's default project id.
    :> json string email: The user's email.

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        {
            "code": 0,
            "description": "User parameter modified."
        }

    :> json int code: the status code
    :> json string description: the error description, present if code is non zero
    """

    endpoints = ['users/parameters']
    parser_arguments = ['user',
                        'project_id',
                        'email',
                        'description']

    def post(self):
        self.logger.info("Received a set parameters request!")
        args = self.parse_args()

        if args["project_id"] is not None:
            projectidstate = self.id_validator(args["project_id"])
            if projectidstate == False:
                self.logger.error("Project id validation failed")
                return AMApiBase.embed_data({}, 1, "Project id validation failed")

        state, user_info = self.get_uuid_and_name(args["user"])
        if state:
            status, message = self._set_params(args, user_info)

            if status:
                self.logger.info("User parameter modified.")
                return AMApiBase.embed_data({}, 0, "")
            else:
                self.logger.error("Internal error in the keystone part: {0}".format(message))
                return AMApiBase.embed_data({}, 1, message)
        else:
            self.logger.error(user_info)
            return AMApiBase.embed_data({}, 1, user_info)

    def _set_params(self, args, user_info):
        if args["project_id"] is not None:
            um_proj_id = self.get_project_id(defaults.PROJECT_NAME)
            if um_proj_id is None:
                self.logger.error("The user management project is not found!")
                return False, "Keystone error, please try again."
            ks_member_roleid = self.get_role_id(defaults.KS_MEMBER_NAME)
            if ks_member_roleid is None:
                self.logger.error("Member user role not found!")
                return False, "Keystone error, please try again."
            if args["project_id"] != um_proj_id and user_info["project"] != args["project_id"]:
                state, message = self.send_role_request_and_check_response(ks_member_roleid, user_info["id"], "put", args["project_id"])
                if not state:
                    self.logger.error("KS error adding project: {0}".format(message))
                    return False, "Keystone error, please try again."
            if user_info["project"] and user_info["project"] != um_proj_id and user_info["project"] != args["project_id"]:
                state, message = self.send_role_request_and_check_response(ks_member_roleid, user_info["id"], "delete", user_info["project"])
                if not state:
                    self.logger.error("KS error removing project: {0}".format(message))
                    return False, "Keystone error, please try again."
        try:
            self.keystone.users.update(user_info["id"], email=args["email"], default_project=args["project_id"])
        except exceptions.http.NotFound as ex:
            self.logger.error("KS NotFound error: {0}".format(ex))
            return False, "This user does not exist in the keystone!"
        except Exception as ex:
            self.logger.error("KS general error: {0}".format(ex))
            return False, "{0}".format(ex)
        return True, "Updated!"
