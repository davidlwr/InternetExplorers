import secrets
import string
import hashlib
import sys

if __name__ == '__main__':  sys.path.append("..")
from Entities.user import User
from DAOs.connection_manager import connection_manager


class user_DAO(object):
    '''
    This class handles connection between app and the database table
    '''

    table_name = "stbern.USER"

    @staticmethod
    def authenticate(username, password):
        '''
        Returns None or User. Authenticates a username and password combination
            User:  Successfull authentication
            None:  Wrong username / password

        Kyeword arguments:
        username -- str
        password -- str
        '''

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor =  connection.cursor()

        try:
            # Check if username exists
            query = "SELECT {} FROM {} WHERE {} = '{}'" \
                .format(User.encrypted_password_token_tname, user_DAO.table_name, User.username_tname, username)
            cursor.execute(query)
            result = cursor.fetchone()
            if result is None: return None   # No username found

            # Get salt, Encrypt given password and authenticate
            salt = result[User.encrypted_password_token_tname]
            encrypted_password = (salt + password).encode('utf-8')
            encrypted_password = hashlib.sha512(encrypted_password).hexdigest()
            query = "SELECT * FROM {} WHERE {} = '{}' AND {} = '{}'" \
                .format(user_DAO.table_name, User.username_tname, username, User.encrypted_password_tname, encrypted_password)

            cursor.execute(query)
            result = cursor.fetchone()

            if result is None: return None  # Auth failed
            else:
                username = result[User.username_tname]
                name = result[User.name_tname]
                email = result[User.email_tname]
                last_sign_in = result[User.last_sign_in_tname]
                staff_type = result[User.staff_type_tname]

                return User(username=username, name=name, email=email, last_sign_in=last_sign_in, staff_type=staff_type)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    # NOTE: On salting and hashing: https://stackoverflow.com/questions/685855/how-do-i-authenticate-a-user-in-php-mysql
    @staticmethod
    def insert_user(user, password):
        '''
        INSERTs a user entry into the database

        Inputs:
        user (Entities.User)
        password (str)
        '''
        # Generate Hash
        alphabet = string.ascii_letters + string.digits
        salt = ''.join(secrets.choice(alphabet) for i in range(20))
        encrypted_password = (salt + password).encode('utf-8')
        encrypted_password = hashlib.sha512(encrypted_password).hexdigest()

        query = "INSERT INTO {} VALUES('{}', '{}', '{}', SHA1('{}'), '{}', '{}', '{}');" \
            .format(user_DAO.table_name, user.username, user.name, user.email, encrypted_password, salt,
                    user.last_sign_in, user.staff_type)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)


    # below to comply with flask-login API
    @staticmethod
    def get_user_by_id(input_username):
        '''
        Returns a User object that corresponds to a row entry in the table, by id
        Returns None if no such id exists
        '''
        query = "SELECT * FROM {} WHERE {} = '{}'".format(user_DAO.table_name, User.username_tname, input_username)

        # Get connection
        factory = connection_manager()
        connection = factory.connection
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchone()

            if result is None: return None 
            else:
                username     = result[User.username_tname]
                name         = result[User.name_tname]
                email        = result[User.email_tname]
                last_sign_in = result[User.last_sign_in_tname]
                staff_type   = result[User.staff_type_tname]
                return User(username=username, name=name, email=email, last_sign_in=last_sign_in, staff_type=staff_type)

        except: raise
        finally: factory.close_all(cursor=cursor, connection=connection)

