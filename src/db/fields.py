import typing as t
from enum import Enum

from peewee import *

ET = t.Type[Enum]


class EnumField(IntegerField):
    """https://github.com/coleifer/peewee/issues/630#issuecomment-459404401"""

    def __init__(self, choices: ET, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)
        self.choices = choices

    def db_value(self, value: ET):
        return value.value

    def python_value(self, value):
        return self.choices(value)
