from bukkitrepo import CONFIG
from datetime import datetime
from pymongo import Connection


class BRConnection(object):
    def __init__(self):
        self.db_info = CONFIG['database']

        self.connection = Connection(self.db_info['host'], self.db_info['port'])

        self.database = self.connection[self.db_info['db']]

        self.users = self.connection[self.db_info['db']].users
        self.deleted_users = self.connection[self.db_info['db']].deleted_users
        self.reset_keys = self.connection[self.db_info['db']].reset_keys


class User(object):
    def __init__(self, email, name, password, verification_key, verified=False, created_at=datetime.now(), role='user'):
        self.data = {'email': email,
                     'name': name,
                     'password': password,
                     'verification_key': verification_key,
                     'verified': verified,
                     'created_at': created_at,
                     'role': role}


class ResetKey(object):
    def __init__(self, user, key, used=False, created_at=datetime.now()):
        self.data = {'user': user,
                     'key': key,
                     'used': used,
                     'created_at': created_at}
