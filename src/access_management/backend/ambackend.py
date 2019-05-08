#!/usr/bin/env python

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

"""
ambackend module
Authorization backend of AM
"""
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from keystoneclient.v3.tokens import TokenManager
from keystoneauth1.exceptions.http import Unauthorized, NotFound

from access_management.db.amdb import AMDatabase, NotExist
import access_management.backend.restlogger as restlog
import access_management.config.defaults as defaults


class AMBackend(object):
    """
    Authorization backend of AM
    """
    def __init__(self, config):
        """
        Creates an instance of the authorization module
        Parses config and creates AMDB instance
        """
        self.config = config
        self.logger = restlog.get_logger(self.config)

        self.db = AMDatabase(db_name=self.config["DB"]["name"], db_addr=self.config["DB"]["addr"],
                             db_port=int(self.config["DB"]["port"]), db_user=self.config["DB"]["user"],
                             db_pwd=self.config["DB"]["pwd"], logger=self.logger)

    def is_authorized(self, token, domain="", domain_object="", method="", role_name=""):
        """
        Does the authorization check
        Validates token and extracts user_id, gets allowed endpoint+method from AMDB

        :param token: keystone token
        :param domain: domian part of the endpoint of the request
        :param domain_object: domain_object part of the endpoint of the request
        :param method: method of the request
        :returns: authorization result
        :rtype: bool
        """

        if domain == "am" and domain_object == "users/ownpasswords":
            return True, ""

        tokenmanager = self.make_auth(token)
        username = ""

        try:
            tokeninfo = tokenmanager.validate(token)
        except Unauthorized as error:
            self.logger.error("Failed to authenticate with given credentials: {}".format(str(error)))
            return False, username
        except NotFound:
            self.logger.error("Unauthorized token")
            return False, username
        except Exception as error:
            self.logger.error("Failure: {}".format(str(error)))
            return False, username

        user_uuid = tokeninfo.user_id
        username = tokeninfo.username
        endpoint = {}
        endpoint["name"] = domain+"/"+domain_object

        if endpoint["name"] != "/":
            self.logger.debug("Endpoint checking")
            try:
                self.db.connect()
            except Exception as error:
                self.logger.error("Failure: {}".format(str(error)))
                return False, username
            try:
                permissions = self.db.get_user_resources(user_uuid)
            except Exception as error:
                self.logger.error("Failure: {}".format(str(error)))
                return False, username
            finally:
                try:
                    self.db.close()
                except Exception as error:
                    self.logger.error("Failure: {}".format(str(error)))
                    return False, username


            endpoint["splitted"] = endpoint["name"].split("/")
            endpoint["length"] = len(endpoint["splitted"])
            for path in permissions:
                per_result = self.check_permission(path, endpoint)
                if per_result:
                    met_result = method in permissions[path]
                    if met_result:
                        self.logger.info("Endpoint authorization successful")
                        return True, username
                    else:
                        self.logger.error("Unauthorized request 1")
                        return False, username
                else:
                    continue

        if role_name != "":
            self.logger.debug("Role checking")
            try:
                self.db.connect()
            except Exception as error:
                self.logger.error("Failure: {}".format(str(error)))
                return False, username
            try:
                permissions = self.db.get_user_roles(user_uuid)
            except Exception as error:
                self.logger.error("Failure: {}".format(str(error)))
                return False, username
            finally:
                try:
                    self.db.close()
                except Exception as error:
                    self.logger.error("Failure: {}".format(str(error)))
                    return False, username

            if role_name in permissions:
                self.logger.info("Role name authorization successful")
                return True, username

        self.logger.error("Unauthorized request 2")
        return False, username

    def check_permission(self, key, endpoint):
        """
        Checks the permission

        :param key: permission from the DB
        :param endpoint: endpoint of the request
        :returns: checking result
        :rtype: bool
        """
        key_splitted = key.split("/")
        key_length = len(key_splitted)
        if key_length == 1 and endpoint["splitted"][0] == key:
            return True
        if endpoint["length"] != key_length:
            return False
        for i in range(0, endpoint["length"]):
            if key_splitted[i][0] == "<":
                continue
            if endpoint["splitted"][i] != key_splitted[i]:
                return False
        return True

    def make_auth(self, token):
        """
        Makes a connection to Keystone for token validation

        :param token: keystone token
        :returns: instance of keystone's TokenManager
        :rtype: TokenManager
        """
        auth = v3.Token(auth_url=self.config["Keystone"]["auth_uri"], token=token, project_name=defaults.PROJECT_NAME, project_domain_id="default")
        sess = session.Session(auth=auth)
        keystone = client.Client(session=sess)
        tokenmanager = TokenManager(keystone)
        return tokenmanager
