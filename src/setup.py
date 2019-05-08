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


from setuptools import setup, find_packages
setup(
    name='access_management',
    version='1.0',
    license='Commercial',
    author='Gabor Illes',
    author_email='gabor.illes@nokia.com',
    platforms=['Any'],
    scripts=[],
    provides=[],
    namespace_packages=['access_management'],
    packages=find_packages(),
    include_package_data=True,
    description='Access Management for Akraino REC blueprint',
    install_requires=['flask', 'flask-restful', 'hostcli'],
    entry_points={
        'console_scripts': [
            'auth-server = access_management.backend.authserver:main',
        ],
        'hostcli.commands': [
            'user create = access_management.cli.cli:CreateNewUser',
            'user delete = access_management.cli.cli:DeleteUsers',
            'user list = access_management.cli.cli:ListUsers',
            'user set password = access_management.cli.cli:ChangeUserPassword',
            'user reset password = access_management.cli.cli:ResetUserPassword',
            'user set parameter = access_management.cli.cli:SetUserParameters',
            'user show = access_management.cli.cli:ShowUserDetails',
            'user showme = access_management.cli.cli:ShowUserOwnDetails',
            'user add role = access_management.cli.cli:AddRoleForUser',
            'user remove role = access_management.cli.cli:RemoveRoleFromUser',
            'user lock = access_management.cli.cli:LockUser',
            'user unlock = access_management.cli.cli:UnlockUser',
            'user add key = access_management.cli.cli:AddKey',
            'user remove key = access_management.cli.cli:RemoveKey',
            'role create = access_management.cli.cli:CreateNewRole',
            'role modify = access_management.cli.cli:ModifyRole',
            'role delete = access_management.cli.cli:DeleteRole',
            'role list all = access_management.cli.cli:ListRoles',
            'role show = access_management.cli.cli:ShowRoleDetails',
            'role list users = access_management.cli.cli:ListUsersOfRole',
            'role add permission = access_management.cli.cli:AddPermissionToRole',
            'role remove permission = access_management.cli.cli:RemovePermissionFromRole',
            'permission list = access_management.cli.cli:ListPermissions',
        ],
    },
    zip_safe=False,
    )
