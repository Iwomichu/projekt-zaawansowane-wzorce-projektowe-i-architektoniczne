from zwpa.UserAuthenticationResult import UserAuthenticationResult


class UserHasNoLoginAttemptsLeft(Exception):
    def __init__(self, user_login: str, authentication_result: UserAuthenticationResult) -> None:
        self.authentication_result = authentication_result
        super().__init__(f"User '{user_login=}' has no logging attempts left")