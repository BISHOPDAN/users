class RCode:
    """
    Response code class
    """

    def __init__(self, code, detail):
        """
        Create a new instance of the class

        :param code: response status code
        :type code: int
        :param detail: response detail
        :type detail: str
        """
        self.code = code
        self.detail = detail


class ApiResponse:
    """
    Response codes
    """
    EMAIL_NOT_VERIFIED = RCode(1001, "Email not verified")
    INVALID_CREDENTIALS = RCode(1002, "Invalid credentials")
    ACCOUNT_NOT_ACTIVE = RCode(1003, "Account not active")
    EMAIL_ALREADY_VERIFIED = RCode(1004, "Email already verified")
