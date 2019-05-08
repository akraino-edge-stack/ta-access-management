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

import re
import os
import json
import traceback
import access_management.db.amdb as amdb
import yarf.restfullogger as logger
from cmframework.apis import cmclient
from keystoneauth1 import session
from keystoneauth1 import exceptions
from keystoneclient.v3 import client
from keystoneauth1.identity import v3
from yarf.restresource import RestResource
from access_management.config.amconfigparser import AMConfigParser
import access_management.config.defaults as defaults


class AMApiBase(RestResource):
    """
    The AMApiBase is the base class that all Access Management REST API endpoints should inherit form. It
    implements some basic helper methods helping the handling of requests.
    """

    def __init__(self):
        super(AMApiBase, self).__init__()
        self.logger = logger.get_logger()
        configparser = AMConfigParser()
        self.config = configparser.parse()
        self.db = amdb.AMDatabase(db_name=self.config["DB"]["name"], db_addr=self.config["DB"]["addr"],
                                    db_port=int(self.config["DB"]["port"]), db_user=self.config["DB"]["user"],
                                    db_pwd=self.config["DB"]["pwd"], logger=self.logger)
        if self.get_token() != "":
            self.keystone = self.auth_keystone()
        self.token = self.get_token()

    @staticmethod
    def error_handler(func):
        def error_handled_function(*args, **kwargs):
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as err:
                traceback_info = traceback.format_exc()
                return AMApiBase.construct_error_response(
                    255,
                    "Server side error:{0}->{1}\nTraceback:\n{2}".format(err.__class__.__name__,
                                                                         err.message,
                                                                         traceback_info))
        return error_handled_function

    @staticmethod
    def construct_error_response(code, description):
        """
        Constructs an error response with the given code and message
        :param code:
        :param message:
        :type code: int
        :type description: str
        :return:
        """
        return AMApiBase.embed_data({}, code, description)

    @staticmethod
    def embed_data(data, code=0, desc=""):
        """
        Embeds the data into the NCIR Restfulframework preferred format.
        :param data: The data to encapsulate, it should be a dictionary
        :param code: The error code, it should be 0 on success. (Default: 0)
        :param desc: The description of the error, if no error happened it can be an empty string.
        :type data: dict
        :type code: int
        :type desc: str
        :return: The encapsulated data as a dictionary.
        :rtype: dict
        """
        return {"code": code,
                "description": desc,
                "data": data}

    def parse_args(self):
        """
        Helper function to handle special cases like all or an empty string
        :return: The parsed arguments with all and empty string replaced with None
        :rtype: dict
        """
        args = self.parser.parse_args()

        for key, value in args.iteritems():
            if value == "all" or value == "":
                args[key] = None
        return args

    def get_user_from_uuid(self, uuid):
        self.logger.debug("Start get_user_from_uuid")
        try:
            s_user = self.keystone.users.get(uuid)
        except exceptions.http.NotFound as ex:
            self.logger.error("{0}".format(ex))
            return 'None', defaults.PROJECT_NAME
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return 'None', defaults.PROJECT_NAME

        name = s_user.name
        try:
            project = s_user.default_project_id
        except AttributeError:
            project = None

        return name, project

    def id_validator(self, uuid):
        if re.match("^[0-9a-f]+$", uuid) is not None:
            return True
        else:
            return False

    def passwd_validator(self, passwd):
        if (re.search(r"^(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[][.,:;/(){}<>~\!?@#$%^&*_=+-])[][a-zA-Z0-9.,:;/(){}<>~\!?@#$%^&*_=+-]{8,255}$", passwd) is None):
            return "The password must have a minimum length of 8 characters (maximum is 255 characters). The allowed characters are lower case letters (a-z), upper case letters (A-Z), digits (0-9), and special characters (][.,:;/(){}<>~\\!?@#$%^&*_=+-). The password must contain at least one upper case letter, one digit and one special character."
        pwd_dict_check = os.system("echo '{0}' | cracklib-check | grep OK &>/dev/null".format(passwd))
        if pwd_dict_check != 0:
            return "The password is incorrect: It cannot contain a dictionary word."
        return None

    def get_role_id(self, role_name):
        self.logger.debug("Start get_role_id")
        try:
            role_list = self.keystone.roles.list()
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)

        for role in role_list:
            if role.name == role_name:
                return str(role.id)

    def get_project_id(self, project_name):
        self.logger.debug("Start get_project_id")
        project_id = None
        try:
            project_list = self.keystone.projects.list()
        except Exception:
            return project_id

        for project in project_list:
            if project.name == project_name:
                return str(project.id)

    def get_uuid_from_token(self):
        self.logger.debug("Start get_uuid_from_token")
        try:
            token_data = self.keystone.tokens.get_token_data(self.get_token())
        except exceptions.http.NotFound as ex:
            self.logger.error("{0}".format(ex))
            return None
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return None
        self.logger.debug({"Token owner": token_data["token"]["user"]["id"]})
        return token_data["token"]["user"]["id"]

    def send_role_request_and_check_response(self, role_id, user_id, method, proj_id):
        try:
            if method == "put":
                self.keystone.roles.grant(role_id, user=user_id, project=proj_id)
            elif method == "delete":
                self.keystone.roles.revoke(role_id, user=user_id, project=proj_id)
            else:
                return False, "Not allowed method for role modification"
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)

        return True, "OK"

    def modify_role_in_keystone(self, role_name, user_id, method, project, need_admin_role = True):
        um_proj_id = self.get_project_id(defaults.PROJECT_NAME)
        if um_proj_id is None:
            message = "The "+defaults.PROJECT_NAME+" project not found!"
            self.logger.error(message)
            return False, message
        role_id = self.get_role_id(role_name)
        if role_id is None:
            message = "{} user role not found!".format(role_name)
            self.logger.error(message)
            return False, message

        state, message = self.send_role_request_and_check_response(role_id, user_id, method, um_proj_id)
        if project and project != um_proj_id:
            state, message = self.send_role_request_and_check_response(role_id, user_id, method, project)

        if need_admin_role and (role_name == defaults.INF_ADMIN_ROLE_NAME or role_name == defaults.OS_ADMIN_ROLE_NAME):
            admin_role_id = self.get_role_id(defaults.KS_ADMIN_NAME)
            if admin_role_id is None:
                message = "The admin user role not found!"
                self.logger.error(message)
                return False, message
            state, message = self.send_role_request_and_check_response(admin_role_id, user_id, method, um_proj_id)
            if project and project != um_proj_id:
                state, message = self.send_role_request_and_check_response(admin_role_id, user_id, method, project)

        return state, message

    def _close_db(self):
        try:
            self.db.close()
        except Exception as err:
            return False, err
        return True, "DB closed"

    def _open_db(self):
        try:
            self.db.connect()
        except Exception as err:
            return False, err
        return True, "DB opened"

    def check_chroot_linux_state(self, username, list_name, state):
        cmc = cmclient.CMClient()
        user_list = cmc.get_property(list_name)
        user_list = json.loads(user_list)
        self.logger.debug("Start the user list check")
        self.logger.debug("Checked {0} user list : {1}".format(list_name, json.dumps(user_list)))
        for val in user_list:
            if val["name"] == username and val["state"] == state:
                self.logger.debug("{0} checked!".format(username))
                return True
        self.logger.debug("{0} failed to check!".format(username))
        return False

    def auth_keystone(self):
        auth = v3.Token(auth_url=self.config["Keystone"]["auth_uri"],
                        token=self.get_token())
        sess = session.Session(auth=auth)
        keystone = client.Client(session=sess)
        return keystone

    def auth_keystone_with_pass(self, passwd, username=None, uuid=None):
        if not username and not uuid:
            return False
        if username:
            auth = v3.Password(auth_url=self.config["Keystone"]["auth_uri"],
                               username=username,
                               password=passwd,
                               project_name=defaults.PROJECT_NAME,
                               user_domain_id="default",
                               project_domain_id="default")
        else:
            auth = v3.Password(auth_url=self.config["Keystone"]["auth_uri"],
                               user_id=uuid,
                               password=passwd,
                               project_name=defaults.PROJECT_NAME,
                               user_domain_id="default",
                               project_domain_id="default")
        sess = session.Session(auth=auth)
        keystone = client.Client(session=sess)
        return keystone

    def get_uuid_and_name(self, user):
        try:
            u_list = self.keystone.users.list()
        except Exception as ex:
            self.logger.error("{0}".format(ex))
            return False, "{0}".format(ex)
        for element in u_list:
            if user == element.id or user == element.name:
                name = element.name
                id = element.id
                project = element.default_project_id
                self.logger.debug("{0},{1},{2}".format(name, id, project))
                return True, {"name": name, "id": id, "project": project}
        self.logger.error("{0} user does not exist in the keystone!".format(user))
        return False, {"{0} user does not exist in the keystone!".format(user)}
