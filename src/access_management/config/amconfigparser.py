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
amconfigparser module
Config parser for AM use
"""
import ConfigParser
import logging

logger = logging.getLogger(__name__)

class AMConfigParser(object):
    """
    Config parser for AM
    """
    cfg_file = '/etc/access_management/am_config.ini'


    def __init__(self, config_file=""):
        """
        Creates an instance of the config parser
        """
        if config_file:
            self.config_path = config_file
        else:
            self.config_path = self.cfg_file

    def parse(self):
        """
        Parses the config
        :return: returns dictionary with config
        :rtype: dict[dict[str]]
        """
        config = ConfigParser.ConfigParser()
        config.read(self.config_path)
        config_dict = {s: dict(config.items(s)) for s in config.sections()}
        return config_dict
