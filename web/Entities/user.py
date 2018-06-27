

class User(object):
    '''
    This class represents a row entry of the DB tables for 'USER'

    Class static variables:
    username_tname                  = "username"
    name_tname                      = "name"
    email_tname                     = "email"
    encrypted_password_tname        = "encrypted_password"
    encrypted_password_token_tname  = "encrypted_password_token"
    last_sign_in_tname              = "last_sign_in"
    staff_type_tname                = "staff_type"
    '''

    username_tname                  = "username"
    name_tname                      = "name"
    email_tname                     = "email"
    encrypted_password_tname        = "encrypted_password"
    encrypted_password_token_tname  = "encrypted_password_token"
    last_sign_in_tname              = "last_sign_in"
    staff_type_tname                = "staff_type"

    STAFF_TYPE_NURSE  = 0
    STAFF_TYPE_DOCTOR = 1

    def __init__(self, username, name, email, staff_type, last_sign_in=None):
        '''
        Constructor method

        Keyword arguments:
        username     -- username for user's account 
        name         -- full name of staff
        email        -- email of staff
        staff_type   -- 0 = nurse, 1 = doctor: See class static vars
        last_sign_in -- last sign in to account (default None)
        '''       
        self.username = username
        self.name = name
        self.email = email
        self.last_sign_in = last_sign_in
        self.staff_type = staff_type

    
    def __str__(self):
        '''
        String representation of object
        '''

        return "USER - username: {}, name: {}, email: {}, last_sign_in: {}, staff_type: {}" \
                .format(self.username, self.name, self.email, self.last_sign_in, self.staff_type)

    
    def __repr__(self):
        '''
        Override python built in function to get string representation of object
        '''
        return self.__str__()