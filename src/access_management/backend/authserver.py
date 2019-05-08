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
import sys

from flask import Flask, request
from flask_restful import Resource, Api
from access_management.backend.ambackend import AMBackend
from access_management.config.amconfigparser import AMConfigParser
import access_management.backend.restlogger as restlog
from werkzeug.exceptions import InternalServerError

app = Flask(__name__)
api = Api(app)


class AuthorizeEndpoint(Resource):
    def post(self):
        backend = AMBackend(config)
        params = json.loads(request.json['params'])
        authorized, username = backend.is_authorized(token=params['token'], domain=params['domain'],
                                                     domain_object=params['domain_object'], method=params['method'])
        return {'authorized': authorized, 'username': username}


class AuthorizeRole(Resource):
    def post(self):
        backend = AMBackend(config)
        authorized, username = backend.is_authorized(token=request.json['token'], role_name=request.json['role'])
        return {'authorized': authorized, 'username': username}


# class DumpTables(Resource):
#     def get(self):
#         backend = AMBackend(config)
#         results = backend.dump_tables()
#         return results


api.add_resource(AuthorizeEndpoint, '/authorize/endpoint')
api.add_resource(AuthorizeRole, '/authorize/role')
# api.add_resource(DumpTables, '/dumptables')


def main():
    global config
    configparser = AMConfigParser("/etc/access_management/am_backend_config.ini")
    config = configparser.parse()
    logger = restlog.get_logger(config)
    initialize(config,logger)
    app.run(host=config["Api"]["host"], port=int(config["Api"]["port"]), debug=True)


def initialize(config, logger):
    logger.info("Initializing...")
    app.register_error_handler(Exception, handle_exp)
    app.before_request(request_logger)
    app.after_request(response_logger)
    app.logger.addHandler(restlog.get_log_handler(config))
    logger.info("Starting up...")


def request_logger():
    app.logger.info('Request: remote_addr: %s method: %s endpoint: %s', request.remote_addr, request.method,
                    request.full_path)


def response_logger(response):
    app.logger.info('Response: status: %s (Associated Request: remote_addr: %s, method: %s, endpoint: %s)',
                    response.status, request.remote_addr, request.method, request.full_path)

    app.logger.debug('Response\'s data: %s', response.data)

    return response


def handle_exp(failure):
    app.logger.error("Internal error: %s ", failure)
    raise InternalServerError()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:# pylint: disable=broad-except
        print "Failure: %s" % error
        sys.exit(255)
