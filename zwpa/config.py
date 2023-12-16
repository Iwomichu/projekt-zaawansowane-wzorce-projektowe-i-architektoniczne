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


class Config(BaseModel):
    admin_login: str
    admin_password: str
    database: DatabaseConfig
    min_days_to_proceed: int = 5

    @staticmethod
    def from_environmental_variables():
        return Config(
            admin_login=os.environ["ZWPA_ADMIN_LOGIN"],
            admin_password=os.environ["ZWPA_ADMIN_PASSWORD"],
            database=DatabaseConfig.from_environmental_variables(),
        )
