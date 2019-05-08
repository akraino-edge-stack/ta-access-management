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

import logging
from logging.handlers import RotatingFileHandler

restlogger = None

class RestLogger(object):
    def __init__(self, config):
        self.logger = logging.getLogger("AM")
        self.logger.setLevel(config["Logging"]["loglevel"])
        self.filehandler = self._get_filehandler(config["Logging"]["logdir"]+"/am.log")
        self.logger.addHandler(self.filehandler)

    @staticmethod
    def _get_filehandler(filename):
        rfh = RotatingFileHandler(filename, mode='a', maxBytes=1000000, backupCount=10, encoding=None, delay=0)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(pathname)s:%(funcName)s:%(lineno)d:%(message)s')
        rfh.setFormatter(formatter)
        return rfh

    def get_logger(self):
        return self.logger

    def get_handler(self):
        return self.filehandler

def get_logger(config):
    global restlogger
    if not restlogger:
        restlogger = RestLogger(config)
    return restlogger.get_logger()

def get_log_handler(config):
    global restlogger
    if not restlogger:
        restlogger = RestLogger(config)
    return restlogger.get_handler()
