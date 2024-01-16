import os
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    host: str
    port: int
    database: str
    login: str
    password: str

    @staticmethod
    def from_environmental_variables():
        return DatabaseConfig(
            host=os.environ["ZWPA_DATABASE_HOST"],
            port=int(os.environ["ZWPA_DATABASE_PORT"]),
            database=os.environ["ZWPA_DATABASE_DATABASE"],
            login=os.environ["ZWPA_DATABASE_LOGIN"],
            password=os.environ["ZWPA_DATABASE_PASSWORD"],
        )


class CartManagerConfig(BaseModel):
    host: str
    port: int
    access_key: str

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @staticmethod
    def from_environmental_variables():
        return CartManagerConfig(
            host=os.environ["ZWPA_CART_MANAGER_HOST"],
            port=int(os.environ["ZWPA_CART_MANAGER_PORT"]),
            access_key=os.environ["ZWPA_CART_MANAGER_ACCESS_KEY"],
        )


class Config(BaseModel):
    admin_login: str
    admin_password: str
    database: DatabaseConfig
    cart_manager_config: CartManagerConfig
    min_days_to_proceed: int = 5

    @staticmethod
    def from_environmental_variables():
        return Config(
            admin_login=os.environ["ZWPA_ADMIN_LOGIN"],
            admin_password=os.environ["ZWPA_ADMIN_PASSWORD"],
            database=DatabaseConfig.from_environmental_variables(),
            cart_manager_config=CartManagerConfig.from_environmental_variables(),
        )
