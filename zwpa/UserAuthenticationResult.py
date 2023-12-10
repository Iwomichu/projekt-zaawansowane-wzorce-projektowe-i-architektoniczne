from dataclasses import dataclass


@dataclass
class UserAuthenticationResult:
    authenticated: bool
    user_id: int | None = None
