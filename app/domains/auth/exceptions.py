class EmailAlreadyExistsError(Exception):
    pass

class AuthException(Exception):
    pass

class PasswordRequiredError(AuthException):
    pass

class InvalidPasswordError(AuthException):
    pass