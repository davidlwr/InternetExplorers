

class User(object):
    '''

    '''

    username_tname                  = "username"
    name_tname                      = "name"
    email_tname                     = "email"
    encrypted_password_tname        = "encrypted_password"
    encrypted_password_token_tname  = "encrypted_password_token"
    last_sign_in_tname              = "last_sign_in"
    staff_type_tname                = "staff_type"

    def __init__(self, username, name, email, last_sign_in, staff_type):
        self.username = username
        self.name = name
        self.email = email
        self.last_sign_in = last_sign_in
        self.staff_type = staff_type

    
    def __str__(self):
        '''
        String representation of object
        '''

        return "USER - username: {}, name: {}, email: {}, last_sign_in: {}, staff_type: {}"
                .format(self.username, self.name, self.last_sign_in, self.staff_type)

    
    def __repr__(self):
        '''
        Override python built in function to get string representation of object
        '''
        return self.__str__()