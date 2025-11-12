import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    SECRET_KEY: str
    APP_DEBUG: bool
    LOGER_LEVEL: str
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


env_settings = EnvSettings()
