import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Protocol


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


class NamingDevice(Protocol):

    def restructure_name(self, name: str):
        return name

    def validate(self, name: str):
        return []


class NsMe:

    def restructure_name(self, name: str):
        return name

    def validate(self, name: str):
        return []


class NsFs:

    def restructure_name(self, name: str):
        return name

    def validate(self, name: str):
        return []


class ProcessingDevice:

    def __init__(self, device: NamingDevice):
        self._device = device

    def restructure_name(self, name: str):
        return self._device.restructure_name(name)

    def validate(self, name: str):
        return self._device.validate(name)


def get_device(device_type: str):
    devices = {
        'ns_me': NsMe,
        'ns_fs': NsFs
    }
    if device_type not in devices:
        raise ValueError(f'Неизвестный тип продукта: {device_type}')
    return devices[device_type]()


env_settings = EnvSettings()
