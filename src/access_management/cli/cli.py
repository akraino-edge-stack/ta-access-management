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

# pylint: disable=line-too-long, too-few-public-methods

import sys
from copy import deepcopy
from hostcli.helper import ListerHelper, ShowOneHelper, CommandHelper
import getpass
import os


API_VERSION =       'v1'
RESOURCE_PREFIX =   'am/%s/' % API_VERSION
DEFAULTPROJECTID =  'default_project_id'
DOMAINID =          'domain_id'
ENABLED =           'enabled'
UUID =              'id'
USER =              'user'
OWNUUID =           'ownid'
USERS =             'users'
LINKS =             'links'
USERNAME =          'username'
NAME =              'name'
OPTIONS =           'options'
PASSWORDEXP =       'password_expires_at'
PASSWORD =          'password'
EMAIL =             'email'
ROLENAME =          'role_name'
ROLEDESC =          'desc'
ROLES =             'roles'
ISSERVICE =         'is_service'
ISCHROOT =          'is_chroot'
NEWPASSWORD =       'npassword'
OLDPASSWORD =       'opassword'
PROJECTID =         'project_id'
PROJECT =           'project'
RESOURCEPATH =      'res_path'
RESOURCEOP =        'res_op'
PERMISSIONNAME =    'permission_name'
PERMISSIONRES =     'resources'
PUBSSHKEY =         'key'
SORT =              'sort'


FIELDMAP = {
    DEFAULTPROJECTID:   {'display': 'Default-Project-ID',
                         'help': 'The ID of the default project for the user.'},
    DOMAINID:           {'display': 'Domain-ID',
                         'help': 'The ID of the domain.'},
    ENABLED:            {'display': 'Enabled',
                         'help': 'Whether the user is able to log in or not.'},
    UUID:               {'display': 'User-ID',
                         'help': 'The user ID.'},
    USER:               {'display': 'User',
                         'help': 'The user ID, or user name.'},
    USERS:              {'display': 'User-IDs',
                         'help': 'List of the user IDs.'},
    LINKS:              {'display': 'Links',
                         'help': 'The links for the user resource.'},
    USERNAME:           {'help': 'The user name.'},
    NAME:               {'display': 'User-Name',
                         'help': 'The user name.'},
    OPTIONS:            {'display': 'Options',
                         'help': 'Options'},
    PASSWORDEXP:        {'display': 'Password-Expires',
                         'help': 'The date and time when the password expires. The time zone is UTC. A null value indicates that the password never expires.'},
    PASSWORD:           {'default': '',
                         'help': 'The password'},
    EMAIL:              {'display': 'E-mail',
                         'help': 'The email'},
    ROLENAME:           {'display': 'Role',
                         'help': 'The role name.'},
    ROLEDESC:           {'display': 'Description',
                         'help': 'The description of the role. It should be enclosed in apostrophes if it contains spaces'},
    ROLES:              {'display': 'Roles',
                         'help': 'The roles of the user.'},
    ISSERVICE:          {'display': 'Immutable',
                         'help': 'Whether the role is a service role. It is non-modifiable.'},
    ISCHROOT:           {'display': 'Log File Access right',
                         'help': 'Permission to use chroot file transfer.'},
    NEWPASSWORD:        {'default': '',
                         'help': 'The new password.'},
    OLDPASSWORD:        {'default': '',
                         'help': 'The old password'},
    PROJECTID:          {'help': 'The ID of the project'},
    PROJECT:            {'help': 'The ID of the project'},
    RESOURCEPATH:       {'help': 'Resource path is the corresponding REST API URL.'},
    RESOURCEOP:         {'help': 'The resource operation'},
    PERMISSIONNAME:     {'display': 'Permission-Name',
                        'help': 'Existing operations for the REST API endpoint.'},
    PERMISSIONRES:      {'display': 'Permission-Resources',
                        'help': 'Path of the REST API endpoint.'},
    PUBSSHKEY:          {'help': 'The public ssh key string itself (not a key file).'},
    SORT:               {'help': 'Comma-separated list of sort keys and directions in the form of <key>[:<asc|desc>]. The direction defaults to ascending if not specified. '
                                 'Sort keys are the case sensitive column names in the command output table. For this command they are: User-ID, User-Name, Enabled and Password-Expires.'}
}

PASSWORDPOLICY_DOCSTRING = """
    The password must have a minimum length of 8 characters (maximum is 255 characters).
    The allowed characters are lower case letters (a-z), upper case letters (A-Z), digits (0-9), and special characters (.,:;/(){}<>~\!?@#$%^&*_=+-).
    The password must contain at least one upper case letter, one digit and one special character.
    The new password is always checked against a password dictionary and it cannot be the same with any of the last 12 passwords already used."""


def password_policy_docstring(a):
    a.__doc__ = a.__doc__.replace("%PASSWORDPOLICY_DOCSTRING%", PASSWORDPOLICY_DOCSTRING)
    return a


class AmCliLister(ListerHelper):
    """Helper class for Lister"""
    def __init__(self, app, app_args, cmd_name=None):
        super(AmCliLister, self).__init__(app, app_args, cmd_name)
        self.fieldmap = deepcopy(FIELDMAP)
        self.resource_prefix = RESOURCE_PREFIX


class AmCliShowOne(ShowOneHelper):
    """Helper class for ShowOne"""
    def __init__(self, app, app_args, cmd_name=None):
        super(AmCliShowOne, self).__init__(app, app_args, cmd_name)
        self.fieldmap = deepcopy(FIELDMAP)
        self.resource_prefix = RESOURCE_PREFIX


class AmCliCommand(CommandHelper):
    """Helper class for Command"""
    def __init__(self, app, app_args, cmd_name=None):
        super(AmCliCommand, self).__init__(app, app_args, cmd_name)
        self.fieldmap = deepcopy(FIELDMAP)
        self.resource_prefix = RESOURCE_PREFIX


@password_policy_docstring
class CreateNewUser(AmCliCommand):
    """A command for creating new user in keystone.
    The password is prompted if not given as parameter.
    %PASSWORDPOLICY_DOCSTRING%"""
    def __init__(self, app, app_args, cmd_name=None):
        super(CreateNewUser, self).__init__(app, app_args, cmd_name)
        self.usebody = True
        self.operation = 'post'
        self.endpoint = 'users'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USERNAME, EMAIL, PASSWORD, PROJECT]
        self.message = 'User created. The UUID is ##id'

    def take_action(self, parsed_args):
        try:
            if parsed_args.password == '':
                password1 = getpass.getpass(prompt='Password: ')
                password2 = getpass.getpass(prompt='Password again: ')
                if password1 == password2:
                    parsed_args.password = password1
                else:
                    raise Exception('New passwords do not match')
            result = self.send_receive(self.app, parsed_args)
            if self.message:
                self.app.stdout.write(ResetUserPassword.construct_message(self.message, result))
        except Exception as exp:
            self.app.stderr.write('Failed with error %s\n' % str(exp))
            sys.exit(1)


class DeleteUsers(AmCliCommand):
    """A command for deleting one or more existing users."""
    def __init__(self, app, app_args, cmd_name=None):
        super(DeleteUsers, self).__init__(app, app_args, cmd_name)
        self.operation = 'delete'
        self.endpoint = 'users'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER]
        self.message = 'User deleted.'


class ListUsers(AmCliLister):
    """A command for listing existing users."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ListUsers, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'users'
        self.positional_count = 0
        self.arguments = [SORT]
        self.columns = [UUID, NAME, ENABLED, PASSWORDEXP]
        self.default_sort = [NAME, 'asc']


@password_policy_docstring
class ChangeUserPassword(AmCliCommand):
    """A command for changing the current user password (i.e. own password).
    The old and new passwords are prompted if not given as parameter.
    %PASSWORDPOLICY_DOCSTRING%"""
    def __init__(self, app, app_args, cmd_name=None):
        super(ChangeUserPassword, self).__init__(app, app_args, cmd_name)
        self.usebody = True
        self.operation = 'post'
        self.endpoint = 'users/ownpasswords'
        #self.mandatory_positional = False
        self.no_positional = True
        self.arguments = [OLDPASSWORD, NEWPASSWORD]
        self.message = 'Your password has been changed.'
        self.auth_required = False

    def take_action(self, parsed_args):
        try:
            if parsed_args.opassword == '':
                parsed_args.opassword = getpass.getpass(prompt='Old password: ')
            if parsed_args.npassword == '':
                npassword1 = getpass.getpass(prompt='New password: ')
                npassword2 = getpass.getpass(prompt='New password again: ')
                if npassword1 == npassword2:
                    parsed_args.npassword = npassword1
                else:
                    raise Exception('New passwords do not match')
            parsed_args.username = os.environ['OS_USERNAME']
            self.arguments.append(USERNAME)
            result = self.send_receive(self.app, parsed_args)
            if self.message:
                self.app.stdout.write(ResetUserPassword.construct_message(self.message, result))
        except Exception as exp:
            self.app.stderr.write('Failed with error %s\n' % str(exp))
            sys.exit(1)


@password_policy_docstring
class ResetUserPassword(AmCliCommand):
    """A command for user administrators for changing other user's password.
    Own password cannot be changed with this command.
    Note that user management admin role is required.
    The new password is prompted if not given as parameter.
    %PASSWORDPOLICY_DOCSTRING%"""
    def __init__(self, app, app_args, cmd_name=None):
        super(ResetUserPassword, self).__init__(app, app_args, cmd_name)
        self.usebody = True
        self.operation = 'post'
        self.endpoint = 'users/passwords'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER, NEWPASSWORD]
        self.message = 'Password has been reset for the user.'

    def take_action(self, parsed_args):
        try:
            if parsed_args.npassword == '':
                npassword1 = getpass.getpass(prompt='New password: ')
                npassword2 = getpass.getpass(prompt='New password again: ')
                if npassword1 == npassword2:
                    parsed_args.npassword = npassword1
                else:
                    raise Exception('New passwords do not match')
            result = self.send_receive(self.app, parsed_args)
            if self.message:
                self.app.stdout.write(ResetUserPassword.construct_message(self.message, result))
        except Exception as exp:
            self.app.stderr.write('Failed with error %s\n' % str(exp))
            sys.exit(1)


class SetUserParameters(AmCliCommand):
    """A command for setting user parameters."""
    def __init__(self, app, app_args, cmd_name=None):
        super(SetUserParameters, self).__init__(app, app_args, cmd_name)
        self.operation = 'post'
        self.endpoint = 'users/parameters'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER, PROJECTID, EMAIL]
        self.message = 'Parameter of the user is changed.'


class ShowUserDetails(AmCliShowOne):
    """A command for displaying the details of a user."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ShowUserDetails, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'users/details'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER]
        self.columns = [DEFAULTPROJECTID, DOMAINID, EMAIL, ENABLED, UUID, LINKS, NAME, OPTIONS, PASSWORDEXP, ROLES]


class ShowUserOwnDetails(AmCliShowOne):
    """A command for displaying the details of a user."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ShowUserOwnDetails, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'users/owndetails'
        self.mandatory_positional = True
        self.positional_count = 0
        self.columns = [DEFAULTPROJECTID, DOMAINID, EMAIL, ENABLED, UUID, LINKS, NAME, OPTIONS, PASSWORDEXP, ROLES]


class AddRoleForUser(AmCliCommand):
    """A command for adding role to a user."""
    def __init__(self, app, app_args, cmd_name=None):
        super(AddRoleForUser, self).__init__(app, app_args, cmd_name)
        self.operation = 'post'
        self.endpoint = 'users/roles'
        self.mandatory_positional = True
        self.positional_count = 2
        self.arguments = [USER, ROLENAME]
        self.message = 'Role has been added to the user.'


class RemoveRoleFromUser(AmCliCommand):
    """A command for removing role from a user."""
    def __init__(self, app, app_args, cmd_name=None):
        super(RemoveRoleFromUser, self).__init__(app, app_args, cmd_name)
        self.operation = 'delete'
        self.endpoint = 'users/roles'
        self.mandatory_positional = True
        self.positional_count = 2
        self.arguments = [USER, ROLENAME]
        self.message = 'Role has been removed from the user.'


class LockUser(AmCliCommand):
    """A command for locking an account."""
    def __init__(self, app, app_args, cmd_name=None):
        super(LockUser, self).__init__(app, app_args, cmd_name)
        self.operation = 'post'
        self.endpoint = 'users/locks'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER]
        self.message = 'User has been locked.'


class UnlockUser(AmCliCommand):
    """A command for enabling a locked account."""
    def __init__(self, app, app_args, cmd_name=None):
        super(UnlockUser, self).__init__(app, app_args, cmd_name)
        self.operation = 'delete'
        self.endpoint = 'users/locks'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER]
        self.message = 'User has been enabled.'


class CreateNewRole(AmCliCommand):
    """A command for creating a new role."""
    def __init__(self, app, app_args, cmd_name=None):
        super(CreateNewRole, self).__init__(app, app_args, cmd_name)
        self.operation = 'post'
        self.endpoint = 'roles'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [ROLENAME, ROLEDESC]
        self.message = 'Role has been created.'


class ModifyRole(AmCliCommand):
    """A command for modifying an existing role."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ModifyRole, self).__init__(app, app_args, cmd_name)
        self.operation = 'put'
        self.endpoint = 'roles'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [ROLENAME, ROLEDESC]
        self.message = 'Role has been modified.'


class DeleteRole(AmCliCommand):
    """A command for deleting one or more existing roles."""
    def __init__(self, app, app_args, cmd_name=None):
        super(DeleteRole, self).__init__(app, app_args, cmd_name)
        self.operation = 'delete'
        self.endpoint = 'roles'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [ROLENAME]
        self.message = 'Role has been deleted.'


class ListRoles(AmCliLister):
    """A command for listing existing roles. Openstack roles won't be listed."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ListRoles, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'roles'
        self.positional_count = 0
        self.arguments = [SORT]
        self.columns = [ROLENAME, ROLEDESC, ISSERVICE, ISCHROOT]
        self.default_sort = [ROLENAME, 'asc']


class ShowRoleDetails(AmCliLister):
    """A command for displaying the details of a role."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ShowRoleDetails, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'roles/details'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [ROLENAME]
        self.columns = [PERMISSIONNAME, PERMISSIONRES]


class ListUsersOfRole(AmCliLister):
    """A command for listing the users of a role."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ListUsersOfRole, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'roles/users'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [ROLENAME]
        self.columns = [ROLENAME, USERS]


class AddPermissionToRole(AmCliCommand):
    """A command for adding a new permission to a role."""
    def __init__(self, app, app_args, cmd_name=None):
        super(AddPermissionToRole, self).__init__(app, app_args, cmd_name)
        self.operation = 'post'
        self.endpoint = 'roles/permissions'
        self.mandatory_positional = True
        self.positional_count = 3
        self.arguments = [ROLENAME, RESOURCEPATH, RESOURCEOP]
        self.message = 'New permission added to role.'


class RemovePermissionFromRole(AmCliCommand):
    """A command for removing a permission from a role."""
    def __init__(self, app, app_args, cmd_name=None):
        super(RemovePermissionFromRole, self).__init__(app, app_args, cmd_name)
        self.operation = 'delete'
        self.endpoint = 'roles/permissions'
        self.mandatory_positional = True
        self.positional_count = 3
        self.arguments = [ROLENAME, RESOURCEPATH, RESOURCEOP]
        self.message = 'Permission deleted from role.'


class ListPermissions(AmCliLister):
    """A command for listing all the permissions and endpoints."""
    def __init__(self, app, app_args, cmd_name=None):
        super(ListPermissions, self).__init__(app, app_args, cmd_name)
        self.operation = 'get'
        self.endpoint = 'permissions'
        self.positional_count = 0
        self.arguments = [SORT]
        self.columns = [PERMISSIONNAME, PERMISSIONRES]
        self.default_sort = [PERMISSIONNAME, 'asc']


class AddKey(AmCliCommand):
    """A command for adding a public ssh key to a user."""
    def __init__(self, app, app_args, cmd_name=None):
        super(AddKey, self).__init__(app, app_args, cmd_name)
        self.operation = 'post'
        self.endpoint = 'users/keys'
        self.mandatory_positional = True
        self.positional_count = 2
        self.arguments = [USER, PUBSSHKEY]
        self.message = 'Key added to the user.'


class RemoveKey(AmCliCommand):
    """A command for removing a public ssh key from a user."""
    def __init__(self, app, app_args, cmd_name=None):
        super(RemoveKey, self).__init__(app, app_args, cmd_name)
        self.operation = 'delete'
        self.endpoint = 'users/keys'
        self.mandatory_positional = True
        self.positional_count = 1
        self.arguments = [USER]
        self.message = 'Key removed from the user.'
