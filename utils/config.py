from __future__ import annotations

import contextlib
import json
import os
from typing import Any

with contextlib.suppress(ImportError):
    from dotenv import dotenv_values, load_dotenv  # type: ignore

    load_dotenv()
    dotenv_values(".env")


def convert_bool(entiry: str) -> bool | None:
    yes = {
        "yes",
        "y",
        "true",
        "t",
        "1",
        "enable",
        "on",
        "active",
        "activated",
        "ok",
        "accept",
        "agree",
    }
    no = {
        "no",
        "n",
        "false",
        "f",
        "0",
        "disable",
        "off",
        "deactive",
        "deactivated",
        "cancel",
        "deny",
        "disagree",
    }

    if entiry.lower() in yes:
        return True
    elif entiry.lower() in no:
        return False

    return None


class Null:
    def __repr__(self) -> str:
        return "Null()"

    def __str__(self) -> str:
        return "Null()"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Null)

    def __getattr__(self, name: str) -> Null:
        return self

    def __getitem__(self, name: str) -> Null:
        return self


ANY = Null | str | list | bool | dict | int | None


class Environment:
    def __init__(self):
        self.__dict = os.environ

    def __getattr__(self, name: str) -> ANY:
        return self.parse_entity(self.__dict.get(name))

    def parse_entity(self, entity: Any, *, to_raise: bool = True) -> ANY:
        #old_entity = entity
        if entity is None:
            return Null()

        entity = str(entity)

        try:
            return json.loads(entity)
        except json.JSONDecodeError:
            pass

        if entity.isdigit():
            return int(entity)

        if _bool := convert_bool(entity):
            return _bool

        if "," in entity:
            # list
            # recursive call
            return [self.parse_entity(e) for e in entity.split(",")]

        return entity

    def __getitem__(self, name: str) -> ANY:
        return self.__getattr__(name)


ENV = Environment()
