from DAOs.connection_manager import connection_manager
import secrets
import string
import hashlib
from Entities.user import User


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

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        with connection.cursor() as cursor:

            # Get salt
            query = "SELECT {} FROM {} WHERE {} = '{}'" \
                .format(User.encrypted_password_token_tname, user_DAO.table_name, User.username_tname, username)
            # print(query)
            cursor.execute(query)
            result = cursor.fetchone()

            if result is None:  # No username found
                return None

            salt = result[User.encrypted_password_token_tname]
            encrypted_password = (salt + password).encode('utf-8')
            encrypted_password = hashlib.sha512(encrypted_password).hexdigest()
            # Encrypt given password and authenticate
            query = "SELECT * FROM {} WHERE {} = '{}' AND {} = '{}'" \
                .format(user_DAO.table_name, User.username_tname, username, User.encrypted_password_tname,
                        encrypted_password)

            cursor.execute(query)
            result = cursor.fetchone()

            if result is None:
                return None
            else:
                username = result[User.username_tname]
                name = result[User.name_tname]
                email = result[User.email_tname]
                last_sign_in = result[User.last_sign_in_tname]
                staff_type = result[User.staff_type_tname]

                return User(username=username, name=name, email=email, last_sign_in=last_sign_in, staff_type=staff_type)

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

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        with connection.cursor() as cursor:
            try:
                cursor.execute(query)
            except Exception as error:
                print(error)
                raise

    # below to comply with flask-login API
    @staticmethod
    def get_user_by_id(input_username):
        '''
        Returns a User object that corresponds to a row entry in the table, by id
        Returns None if no such id exists
        '''
        query = "select * from {} where {} = '{}'".format(user_DAO.table_name, User.username_tname, input_username)
        # print(query)

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

            if result is None:
                return None
            else:
                username = result[User.username_tname]
                name = result[User.name_tname]
                email = result[User.email_tname]
                last_sign_in = result[User.last_sign_in_tname]
                staff_type = result[User.staff_type_tname]

                return User(username=username, name=name, email=email, last_sign_in=last_sign_in, staff_type=staff_type)

# # # TESTS
# dao = user_DAO()

# # # Insert
# user = User("usernayme", "nayme", "emayle", "1", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
# dao.insert_user(user, "password1234")
# print("insert done...")

# # # Authenticate
# user = dao.authenticate("usernayme", "password1234")
# print(user)
# print("auth done...")

# r = dao.authenticate(username="xXxiao_shadow_flamezXx", password='wrong_pass')
