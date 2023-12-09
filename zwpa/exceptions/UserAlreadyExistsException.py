class UserAlreadyExistsException(Exception):
    def __init__(self, user_login: str) -> None:
        super().__init__(f"User '{user_login=}' already taken")