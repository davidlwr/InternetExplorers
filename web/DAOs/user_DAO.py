sys.path.append("..")
from Entities.user import User

class user_DAO(object):
    '''
    This class handles connection between app and the database table
    '''

    table_name = "stbern.USER"

    def authenticate(self, username, password):
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
            query = "SELECT {} FROM {} WHERE {} = {}"      \
                        .format(User.encrypted_password_token_tname, table_name, User.username_tname, username)

            cursor.execute(query)
            result = cursor.fetchone()

            if len(result) <= 0:    # No username found
                return None
            
            salt = result[User.encrypted_password_token_tname]
            
            # Encrypt given password and authenticate
            query = "SELECT * FROM {} WHERE {} = {} AND {} = SHA1(CONCAT({}, {})"
                        .format(table_name, User.username_tname, username, User.encrypted_password_tname, salt, password)


            cursor.execute(query)
            result = cursor.fetchone()

            if len(result) <= 0:
                return None
            else:
                username = result[User.username_tname]
                name = result[User.name_tname]
                email = result[User.email_tname]
                last_sign_in = result[User.last_sign_in_tname]
                staff_type = result[User.staff_type_tname]

                return User(username=username, name=name, email=email, last_sign_in=last_sign_in, staff_type=staff_type)


    # NOTE: On salting and hasing: https://stackoverflow.com/questions/685855/how-do-i-authenticate-a-user-in-php-mysql
    def insert_user(self, user, password):
        '''
        INSERTs a user entry into the database
        '''

        query = """
                SET @salt = SUBSTRING(SHA1(RAND()), 1, 6)
                INSERT INTO {} VALUES {}, {}, {}, SHA1(CONCAT(@salt, {})), @salt, {}, {}"""
                    .format(table_name, user.username, user.name, user.email, password, user.last_sign_in, user.staff_type)

        # Get connection, which incidentally closes itself during garbage collection
        factory = connection_manager()
        connection = factory.connection

        with connection.cursor() as cursor:
            try:
                cursor.execute(query)
            except Exception as error:
                print(error)
                raise


    