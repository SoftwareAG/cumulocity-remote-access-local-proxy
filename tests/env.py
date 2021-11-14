"""Test environment"""

import os
from typing import Any, Dict
from c8ylp.env import loadenv


class Environment:
    def __init__(self, file=".env") -> None:
        loadenv(file)

        self.data = os.environ

    def env(self) -> Dict[str, str]:
        return self.data

    def create_empty_env(self) -> Dict[str, Any]:
        empty_env = {}
        for key in self.data:
            if key.startswith("C8Y"):
                empty_env[key] = None
        return empty_env

    def create_authenticated(self) -> Dict[str, Any]:
        return {
            "C8Y_HOST": "https://example.c8y.io",
            "C8Y_TENANT": "t12345",
            "C8Y_USER": "user01",
            "C8Y_TOKEN": "dummy-token",
        }

    def create_username_password(self) -> Dict[str, Any]:
        return {
            "C8Y_HOST": "https://example.c8y.io",
            "C8Y_TENANT": "t12345",
            "C8Y_USER": "user01",
            "C8Y_PASSWORD": "som4-p4$swurd",
        }


ENV = Environment()
