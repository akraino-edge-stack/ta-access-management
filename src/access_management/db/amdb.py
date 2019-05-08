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
amdb module
Maintains AM database
"""

from peewee import Model
from peewee import MySQLDatabase
from peewee import CharField, BooleanField, ForeignKeyField
from peewee import DoesNotExist

AM_DB = MySQLDatabase(None)


class BaseAMModel(Model):
    """
    Base model for AM database
    """

    class Meta(object):
        database = AM_DB


class AMdbUser(BaseAMModel):
    user_uuid = CharField(null=False, unique=True)
    name = CharField(null=False, unique=True)
    is_service = BooleanField(default=False)
    email = CharField(default='')

    class Meta(object):
        db_table = 'user'


class AMdbResource(BaseAMModel):
    path = CharField(null=False)
    op = CharField(null=False)
    desc = CharField(default='')

    class Meta(object):
        db_table = 'resource'


class AMdbRole(BaseAMModel):
    name = CharField(null=False, unique=True)
    is_service = BooleanField(default=False)
    is_chroot = BooleanField(default=False)
    desc = CharField(default='')

    class Meta(object):
        db_table = 'role'


class AMdbRoleResource(BaseAMModel):
    role_id = ForeignKeyField(AMdbRole, to_field='id', db_column='role_id')
    res_id = ForeignKeyField(AMdbResource, to_field='id', db_column='res_id')

    class Meta(object):
        db_table = 'role_resource'


class AMdbUserRole(BaseAMModel):
    user_id = ForeignKeyField(AMdbUser, to_field='id', db_column='user_id')
    role_id = ForeignKeyField(AMdbRole, to_field='id', db_column='role_id')

    class Meta(object):
        db_table = 'user_role'


class NotExist(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AlreadyExist(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NotAllowedOperation(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AMDatabase(object):
    """ AM Database handler class """

    def __init__(self, db_name, db_user, db_pwd, db_addr, db_port, logger, management_mode=False):
        """
        Creates an instance of AM database

        :param db_name: Name of AM's MySQL database
        :param db_user: Username of the MySQL user
        :param db_pwd: Password of the MySQL user
        :param db_addr: Address of the MySQL server
        :param db_port: Port of the MySQL server (type int)
        :param logger: Logger instance to be used

        :Example:
        db = AMDatabase(db_name='am_database',db_addr='127.0.0.1',
                         db_port=3306, db_user='db_user',db_pwd='db_pwd',
                         logger=logging.getLogger("Example"))
        db.connect()
        # do your code here
        db.close()
        """
        self.db_name = db_name
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_host = db_addr
        self.db_port = db_port
        self.am_db = AM_DB
        self.management_mode = management_mode

        if logger is None:
            raise Exception("You did not give me a logger to use. That's a no-no!")
        else:
            self.logger = logger

    def connect(self):
        """
        Connects to the database
        :raise Exception on failure
        """

        try:
            self.am_db.init(self.db_name,
                            host=self.db_host, port=self.db_port,
                            user=self.db_user, password=self.db_pwd)
            self.am_db.connect()
            self.logger.debug('Connected to database')
        except Exception as ex:
            self.logger.error('Error occured while connecting to database')
            raise Exception('Error occured while connecting to database')

    def close(self):
        """
        Closes the database connection
        :raise Exception on failure
        """

        try:
            self.am_db.close()
            self.logger.debug('Database closed')
        except Exception as ex:
            self.logger.error('Error closing connection to database')
            raise Exception('Error closing connection to database')

    def create_tables(self):
        self.am_db.create_tables([AMdbUser, AMdbRole, AMdbResource, AMdbUserRole, AMdbRoleResource], safe=True)
        # AMdbUser.create_table(safe=True)
        # AMdbRole.create_table(safe=True)
        # AMdbResource.create_table(safe=True)
        # AMdbUserRole.create_table(safe=True)
        # AMdbRoleResource.create_table(safe=True)

    def create_user(self, uuid, name, em='', service=False):
        """
        Creates a user with a UUID and optional email parameter

        :param uuid: User identifier
        :param name: User name
        :param em: email
        :param service: is_service parameter value
        :return: returns AMdbUser instance
        :rtype AMdbUser
        :raise AlreadyExist on failure
        """

        self.logger.debug('Called DB function: create_user')
        query = (AMdbUser.select().where((AMdbUser.user_uuid == uuid) | (AMdbUser.name == name)))
        query.execute()
        if query.namedtuples():
            raise AlreadyExist(
                'User already exists in table: {0}'.format(uuid))
        if service:
            user = AMdbUser.create(user_uuid=uuid, name=name, is_service=self.management_mode, email=em)
        else:
            user = AMdbUser.create(user_uuid=uuid, name=name, is_service=False, email=em)
        return user

    def get_user(self, uuid):
        """
        Returns the user record based on user UUID

        :return: returns AMdbUser instance created
        :raise NotExist on failure
        """
        self.logger.debug('Called DB function: get_user')
        try:
            return AMdbUser.get(AMdbUser.user_uuid == uuid)
        except DoesNotExist:
            raise NotExist('User does not exist: {0}'.format(uuid))

    def delete_user(self, uuid):
        """
        Deletes user; also removes reference from other tables

        :param uuid: user id
        :raise NotAllowedOperation if user is service user
        """
        self.logger.debug('Called DB function: delete_user')
        try:
            user = self.get_user(uuid)
        except NotExist as ex:
            raise NotExist(ex)

        if user.is_service and not self.management_mode:
            raise NotAllowedOperation(
                'Deleting service user is not allowed: {0}'.format(uuid))
        query = (AMdbUserRole
                 .delete().where(AMdbUserRole.user_id == user.id))
        query.execute()
        query = (AMdbUser.delete().where(AMdbUser.user_uuid == uuid))
        query.execute()

    def set_user_param(self, uuid, email=''):
        """
        Sets extra parameters for users
        :param uuid: user identifier
        :param email: email address of the user
        :raise  NotAllowedOperation if the user is a service user
        """
        self.logger.debug('Called DB function: set_user_param')
        try:
            user = self.get_user(uuid)
        except NotExist as ex:
            raise NotExist(ex)

        if user.is_service and not self.management_mode:
            raise NotAllowedOperation(
                'Modifying service user is not allowed: {0}'.format(uuid))
        query = (AMdbUser
                 .update({AMdbUser.email: email})
                 .where(AMdbUser.user_uuid == uuid))
        query.execute()

    def get_all_users(self):
        """
        Returns all of the users

        :return: Values are in a dict
        :rtype: dict
        """
        self.logger.debug('Called DB function: get_all_users')
        query = (AMdbUser.select(AMdbUser.user_uuid,
                                 AMdbUser.is_service,
                                 AMdbUser.email))
        query.execute()
        ret = {}
        for user in query.namedtuples():
            ret[user.user_uuid] = {'user_uuid': user.user_uuid,
                                   'is_service': user.is_service,
                                   'email': user.email}
        return ret

    def create_role(self, role_name, role_desc='', is_chroot=False):
        """
        Creates role

        :param role_name: role name
        :param role_desc: description of the role
        :param is_chroot: is_chroot value
        :return: returns AMdbRole instance created
        :rtype: AMdbRole
        :raise AlreadyExist if the role is already present
        """
        self.logger.debug('Called DB function: create_role')
        query = (AMdbRole.select().where(AMdbRole.name == role_name))
        query.execute()
        if query.namedtuples():
            raise AlreadyExist(
                'Role already exists in table: {0}'.format(role_name))
        role = AMdbRole.create(name=role_name, desc=role_desc, is_chroot=is_chroot, is_service=self.management_mode)
        return role

    def get_role(self, role_name):
        """
        Gets role by role name

        :param role_name: role name
        :return: AMdbRole instance
        :rtype: AMdbRole
        :raise NotExist if role not exist
        """
        self.logger.debug('Called DB function: get_role')
        try:
            return AMdbRole.get(AMdbRole.name == role_name)
        except DoesNotExist:
            raise NotExist('Role does not exsist: {}'.format(role_name))

    def delete_role(self, role_name):
        """
        Deletes role by role name;
        also removes from role_resource and user_role table

        :param role_name: role name
        :raise NotAllowedOperation if role is service role
        """
        self.logger.debug('Called DB function: delete_role')
        role = self.get_role(role_name)
        if role.is_service and not self.management_mode:
            raise NotAllowedOperation(
                'Deleting service role is not allowed: {0}'.format(role_name))
        query = (AMdbUserRole
                 .delete().where(AMdbUserRole.role_id == role.id))
        query.execute()
        query = (AMdbRoleResource
                 .delete().where(AMdbRoleResource.role_id == role.id))
        query.execute()
        query = (AMdbRole.delete().where(AMdbRole.id == role.id))
        query.execute()

    def set_role_param(self, role_name, desc=None, is_chroot=False):
        """
        Sets role optional parameters

        :param role_name: role name
        :param desc: role description
        :param is_chroot: is_chroot value
        :raise NotAllowedOperation if role is service role
        """
        self.logger.debug('Called DB function: set_role_param')
        role = self.get_role(role_name)
        if role.is_service and not self.management_mode:
            raise NotAllowedOperation(
                'Modifying service role is not allowed: {0}'.format(role_name))
        query = (AMdbRole
                 .update({AMdbRole.desc: desc, AMdbRole.is_chroot: is_chroot, AMdbRole.is_service: self.management_mode})
                 .where(AMdbRole.name == role_name))
        query.execute()

    def get_all_roles(self):
        """
        Returns all roles in a dict

        :return: Values are in a dict
        :rtype: dict
        """
        self.logger.debug('Called DB function: get_all_roles')
        roles = AMdbRole.select()
        res = {}
        for role in roles:
            res[role.name] = {'role_name': role.name,
                              'is_service': role.is_service,
                              'desc': role.desc,
                              'is_chroot': role.is_chroot}
        return res

    def is_chroot_role(self, role_name):
        """
        Checks if the role is a chroot role or not

        :param role_name: role name
        :return: bool; true if role is chroot role
        """
        self.logger.debug('Called DB function: is_chroot_role')
        role = self.get_role(role_name)
        return role.is_chroot

    def get_resource_with_operations(self, res_path):
        """
        Gets resource by resource name
        returns a dict: key is the resource path,
        values are allowed operations in a list
        In other words: returns the allowed operations on a resource

        :param res_path: resource path
        :raise NotExist if the resource is not present
        :returns dict where resource is the key, values are the operations
        """
        self.logger.debug('Called DB function: get_resource_with_operations')
        query = (AMdbResource.select().where(AMdbResource.path == res_path))
        query.execute()
        res = dict()
        if not query.namedtuples():
            raise NotExist('Resource does not exist: {0}'.format(res_path))
        for row in query.namedtuples():
            if row[1] not in res.keys():
                res[row[1]] = [row[2]]
            else:
                res[row[1]].append(row[2])
        return res

    def get_resource(self, res_path, res_op):
        """
        Gets resource by resource name and path

        :param res_path: resource path
        :param res_op: operation
        :returns: AMdbResource instance
        :rtype AMdbResource
        :raise NotExist if resource is not present
        """
        self.logger.debug('Called DB function: get_resource')
        try:
            return AMdbResource.get(AMdbResource.path == res_path,
                                    AMdbResource.op == res_op)
        except DoesNotExist:
            raise NotExist('Resource {0} with op {1} does not exsist'
                           .format(res_path, res_op))

    def get_resources(self):
        """
        Gets all resources with operations

        :returns: dict[str:list[str]] values
        :rtype dict
        """
        self.logger.debug('Called DB function: get_resources')
        resources = AMdbResource.select()
        ret = dict()
        for res in resources:
            if res.path not in ret.keys():
                ret[res.path] = [res.op]
            else:
                ret[res.path].append(res.op)
        return ret

    def add_user_role(self, uuid, role_name):
        """
        Adds a role to a user

        :param uuid: user identifier
        :param role_name: name of the role
        :raise AlreadyExist if the user-role is already present,
        NotAllowedOperation if the user is a service user
        """

        self.logger.debug('Called DB function: add_user_role')
        try:
            user = self.get_user(uuid)
        except NotExist as ex:
            raise NotExist(ex)

        if user.is_service and not self.management_mode:
            raise NotAllowedOperation(
                'Service user roles cannot be modified: {0}'.format(uuid))
        role = self.get_role(role_name)
        query = (AMdbUserRole.select()
                 .where(AMdbUserRole.user_id == user.id,
                        AMdbUserRole.role_id == role.id))
        query.execute()
        if query.namedtuples():
            raise AlreadyExist('Role for user already exists in table: {0}:{1}'
                               .format(uuid, role_name))
        else:
            query = (AMdbUserRole
                     .insert({AMdbUserRole.user_id: user.id,
                              AMdbUserRole.role_id: role.id}))
            query.execute()

    def delete_user_role(self, uuid, role_name):
        """
        Deletes role for a given user (removes permission).
        Does not delete the role itself.

        :param uuid: user identifier
        :param role_name: name of the role
        :raise NotExist if the user has no such role,
        NotAllowedOperation if the user is a service user
        """
        self.logger.debug('Called DB function: delete_user_role')
        try:
            user = self.get_user(uuid)
        except NotExist as ex:
            raise NotExist(ex)

        if user.is_service and not self.management_mode:
            raise NotAllowedOperation(
                'Service user roles cannot be modified: {0}'.format(uuid))
        role = self.get_role(role_name)
        query = (AMdbUserRole
                 .delete().where(AMdbUserRole.user_id == user.id,
                                 AMdbUserRole.role_id == role.id))
        ret = query.execute()
        if ret == 0:
            raise NotExist('User {0} has no role {1}.'
                           .format(user.user_uuid, role_name))

    def get_user_roles(self, uuid):
        """
        Gets role belonging to a user

        :param uuid: user identifier
        :returns: list of roles for the user
        :rtype: list[str]
        """
        self.logger.debug('Called DB function: get_user_roles')
        try:
            user = self.get_user(uuid)
        except NotExist as ex:
            raise NotExist(ex)

        query = (AMdbUserRole.select()
                 .where(AMdbUserRole.user_id == user.id)
                 ).join(AMdbRole).where(AMdbRole.id == AMdbUserRole.role_id
                                        ).select(AMdbRole.name)
        res = []
        for row in query.namedtuples():
            res.append(row[0])
        return res

    def get_user_resources(self, uuid):
        """
        Gets resources belonging to a user, returns a list of resources
        returns a dict whith resource path as keys,
        allowed operations as values in a list

        :param uuid: user identifier
        :returns: a dict where the keys are resource names,
        values are the operations in a list
        :rtype: dict[str:list[str]]
        """
        self.logger.debug('Called DB function: get_user_resources')
        try:
            user = self.get_user(uuid)
        except NotExist as ex:
            raise NotExist(ex)

        roles = AMdbUserRole.select().where(
            AMdbUserRole.user_id == user.id)
        res = dict({})
        for role_row in roles:
            role_res = AMdbRoleResource.select().where(
                AMdbRoleResource.role_id == role_row.role_id)
            for r_res_row in role_res:
                if r_res_row.res_id.path not in res.keys():
                    res[r_res_row.res_id.path] = [r_res_row.res_id.op]
                else:
                    res[r_res_row.res_id.path].append(r_res_row.res_id.op)
        return res

    def add_resource_to_role(self, role_name, res_path, res_op):
        """
        Assings a resource+operation to a role

        :param role_name: role name
        :param res_path: resource path
        :param res_op: resource operation
        :raise AlreadyExist if there's such a pairing,
        NotAllowedOperation if the role is a service role
        """
        self.logger.debug('Called DB function: add_resource_to_role')
        role = self.get_role(role_name)
        if role.is_service and not self.management_mode:
            raise NotAllowedOperation('Service role cannot be modified: {0}'
                                      .format(role_name))
        res = self.get_resource(res_path, res_op)
        query = (AMdbRoleResource.select().where(
            AMdbRoleResource.role_id == role.id,
            AMdbRoleResource.res_id == res.id))
        query.execute()
        if query.namedtuples():
            raise AlreadyExist(
                'Role-resource already exists in table: {0}:{1}, {2}'
                .format(role_name, res_path, res_op))
        else:
            query = (AMdbRoleResource
                     .insert({AMdbRoleResource.role_id: role.id,
                              AMdbRoleResource.res_id: res.id}))
            query.execute()

    def get_role_resources(self, role_name):
        """
        Gets resources belonging to a role (like giving permission)

        :param role_name: role name
        :returns: dictionary, where keys are resource paths and values are
        operations in a list
        :rtype: dict[str:list[str]]
        """
        self.logger.debug('Called DB function: get_role_resources')
        role = self.get_role(role_name)
        query = (AMdbRoleResource.select()
                 .where(AMdbRoleResource.role_id == role.id)
                 .join(AMdbResource)
                 .where(AMdbResource.id == AMdbRoleResource.res_id)
                 ).select(AMdbResource.path, AMdbResource.op)
        query.execute()
        res = dict()
        for row in query.namedtuples():
            if row[0] not in res.keys():
                res[row[0]] = [row[1]]
            else:
                res[row[0]].append(row[1])
        return res

    def delete_role_resource(self, role_name, res_path, res_op):
        """
        Deletes a resource from a role (like removing permission)
        :param role_name: role name
        :param res_path: resource path
        :param res_op: resource operation
        """
        self.logger.debug('Called DB function: delete_role_resource')
        role = self.get_role(role_name)
        if role.is_service and not self.management_mode:
            raise NotAllowedOperation('Service role cannot be modified: {0}'
                                      .format(role_name))
        res = self.get_resource(res_path, res_op)
        query = (AMdbRoleResource.delete()
                 .where(AMdbRoleResource.role_id == role.id,
                        AMdbRoleResource.res_id == res.id))
        ret = query.execute()
        if not ret:
            raise NotExist('Role {0} has no such resource:operation : {1}:{2}'
                           .format(role_name, res_path, res_op))

    def create_resource(self, res_path, res_op, res_desc=''):
        """ Creates resource """
        self.logger.debug('Called DB function: create_resource')
        if self.management_mode:
            q = (AMdbResource.select().where(AMdbResource.path == res_path, AMdbResource.op == res_op))
            q.execute()
            if len(q.namedtuples()) > 0:
                print 'Resource and operation already exists in table'
                raise Exception(res_path+':'+res_op)
            resource = AMdbResource.create(path=res_path, op=res_op, desc=res_desc)
            return resource

    def update_resource(self, res_path, res_op, res_desc):
        """ updates resource """
        self.logger.debug('Called DB function: update_resource')
        if self.management_mode:
            q = (AMdbResource.select().where(AMdbResource.path == res_path, AMdbResource.op == res_op))
            q.execute()
            if len(q.namedtuples()) == 0:
                print 'Resource does not exist'
                raise Exception(res_path+":"+res_op)
            q = (AMdbResource.update({AMdbResource.desc: res_desc})
                 .where(AMdbResource.path == res_path, AMdbResource.op == res_op))
            q.execute()

    def get_user_uuid(self, name):
        """
        Returns the user UUID based on user name

        :return: returns UUID
        :raise NotExist on failure
        """
        self.logger.debug('Called DB function: get_user_uuid')
        try:
            return AMdbUser.get(AMdbUser.name == name).user_uuid
        except DoesNotExist:
            raise NotExist('User does not exist: {0}'.format(name))

    def get_user_name(self, uuid):
        """
        Returns the user name based on user UUID

        :return: returns username
        :raise NotExist on failure
        """
        self.logger.debug('Called DB function: get_user_name')
        try:
            return AMdbUser.get(AMdbUser.user_uuid == uuid).name
        except DoesNotExist:
            raise NotExist('User does not exist: {0}'.format(uuid))

    def get_role_users(self, role_name):
        """
        Gets users associated to a given role
        :param role_name: role name
        :returns list containing uuids; if there are no users
        associated to the role, an empty list
        :rtype list[str]
        :raise AlreadyExist if there's no such role
        """
        self.logger.debug('Called DB function: get_role_users')
        role = self.get_role(role_name)
        query = (AMdbUserRole.select(AMdbUserRole.user_id)
                 .where(AMdbUserRole.role_id == role.id)
                 .join(AMdbUser).where(AMdbUser.id == AMdbUserRole.user_id))
        res = query.execute()
        return [row.user_id.user_uuid for row in res]

    def get_user_table(self):
        """
        Gets user table
        :returns list of each row in dict format
        :rtype list[dict]
        """
        result = []
        query = AMdbUser.select().dicts()
        for row in query:
            result.append(row)
        return result

    def get_role_table(self):
        """
        Gets role table
        :returns list of each row in dict format
        :rtype list[dict]
        """
        result = []
        query = AMdbRole.select().dicts()
        for row in query:
            result.append(row)
        return result

    def get_resource_table(self):
        """
        Gets resource table
        :returns list of each row in dict format
        :rtype list[dict]
        """
        result = []
        query = AMdbResource.select().dicts()
        for row in query:
            result.append(row)
        return result

    def get_user_role_table(self):
        """
        Gets user_role table
        :returns list of each row in dict where ids are replaced:
        user_id -> user.name
        role_id -> role.name
        :rtype list[dict]
        """
        result = []
        query = AMdbUserRole.select(AMdbUser.name.alias('user_name'), AMdbRole.name.alias('role_name'))\
            .join(AMdbUser).switch(AMdbUserRole).join(AMdbRole).dicts()
        result = [row for row in query]
        return result

    def get_role_resource_table(self):
        """
        Gets role_resource table
        :returns list of each row in dict where ids are replaced:
        role_id -> role.name
        res_id -> resource.path + resource.op
        :rtype list[dict]
        """
        result = []
        query = AMdbRoleResource.select(AMdbRole.name, AMdbResource.path, AMdbResource.op)\
            .join(AMdbRole).switch(AMdbRoleResource).join(AMdbResource).dicts()
        result = [row for row in query]
        return result

    def get_roles_for_permission(self, perm_name, op):
        """
        Gets all roles where the permission is included
        :returns list of role
        perm_name -> resource.name
        op -> resource.op
        :rtype list[str]
        """
        self.logger.debug('Called DB function: get_roles_for_permission')
        result = []
        res_id = self.get_resource(perm_name, op).id
        query = AMdbRoleResource.select(AMdbRole.name).join(AMdbRole).where(AMdbRoleResource.res_id == res_id).dicts()
        for row in query:
            result.append(row["name"])
        return result

    def get_all_role_perms(self):
        """
        Gets all roles/permissions where the permission is included
        :returns hashmap of permission, operation+roles
        :rtype dict
        """
        self.logger.debug('Called DB function: get_all_role_perms')
        result = {}
        res_lst = self.get_resources()
        query = AMdbResource.select(AMdbResource.path, AMdbResource.op).dicts()
        for row in query:
            result[row["path"]+":"+row["op"]] = self.get_roles_for_permission(row["path"], row["op"])
        return result
