#  MIT License
#
#  Copyright (c) 2022 tooboredtocode
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import os
import typing
from typing import Mapping, Optional, TypeVar, Union

from config_parser.loader import ParsedValue


class InvalidConfigError(Exception):
    pass


class MissingEnvVar(Exception):
    pass


T = TypeVar("T")


def new_str_func(self: object) -> str:
    return f"{self.__class__.__name__}[{', '.join(f'{item}: {value}' for item, value in self.__dict__.items())}]"


class Parser:

    def __init__(self, data: Mapping[str, ParsedValue], env_tag: Optional[str] = "!ENV") -> None:
        self._data = data
        self._env_tag = env_tag

    @staticmethod
    def populate_attributes(source: ParsedValue, to_type: T, key: str, env_tag: str) -> T:
        if to_type in [str, int, float]:
            if (
                isinstance(source, str) and
                source.startswith("!ENV")
            ):
                tag, flag, *extra = source.split(" ")

                var = os.environ.get(flag)
                if var:
                    source = var
                elif extra:
                    source = " ".join(extra)
                else:
                    raise MissingEnvVar(f"Could not find env var {flag}")

            return to_type(source)

        origin_type = typing.get_origin(to_type)
        generic_types = [
            generic_type
            for generic_type in typing.get_args(to_type)
            if generic_type is not type(None)
        ]

        if origin_type is Union:
            for try_, generic_type in enumerate(generic_types):
                try:
                    return generic_type(source)
                except ValueError:
                    if try_ == len(generic_types) - 1:
                        raise

        if origin_type is list:
            if not isinstance(source, list):
                raise InvalidConfigError(
                    f"Found incompatible type {type(source).__name__} instead of list "
                    f"for key: {key}"
                )

            result = []
            list_type = generic_types[0]

            for index, item in enumerate(source):
                result.append(Parser.populate_attributes(item, list_type, f"{key}.{index}", env_tag))

            return result

        result = to_type()
        for attribute, attribute_type in to_type.__annotations__.items():
            if not isinstance(source, Mapping):
                raise InvalidConfigError(
                    f"Found incompatible type {type(source).__name__} instead of {attribute_type.__name__} "
                    f"for key: {key}"
                )

            new_key = f"{key + '.' if key else ''}{attribute}"

            try:
                value = source[attribute]
            except KeyError as err:
                if (
                    typing.get_origin(attribute_type) is Union and
                    type(None) in typing.get_args(attribute_type)
                ):
                    value = getattr(to_type, attribute, None)
                else:
                    raise InvalidConfigError(f"Could not find key {new_key} in config") from err

            setattr(
                result,
                attribute,
                Parser.populate_attributes(value, attribute_type, new_key, env_tag)
            )

        to_type.__str__ = new_str_func
        to_type.__repr__ = new_str_func
        return result

    def create_config(self, config_class: T) -> T:
        return Parser.populate_attributes(self._data, config_class, "", self._env_tag)
