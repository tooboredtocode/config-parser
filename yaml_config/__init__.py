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
from pathlib import Path
from typing import Any, Dict, Callable, List, Optional, Union, TypeVar

import yaml


class InvalidConfigError(Exception):
    pass


T = TypeVar("T")


def _env_var_constructor(loader, node):
    default = None

    # Check if the node is a plain string value
    if node.id == "scalar":
        value = loader.construct_scalar(node)
        key = str(value)
    else:
        # The node value is a list
        value = loader.construct_sequence(node)

        if len(value) >= 2:
            # If we have at least two values, then we have both a key and a default value
            default = value[1]
            key = value[0]
        else:
            # Otherwise, we just have a key
            key = value[0]

    return os.getenv(key, default)


class Config:

    def __init__(self, location: str, env_tag: Optional[str] = "!ENV"):
        config_path = Path(location)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Cannot find config! Please place it here: {config_path}"
            )

        yaml.SafeLoader.add_constructor(env_tag, _env_var_constructor)

        with open(config_path, encoding="UTF-8") as file:
            self._cfg = yaml.safe_load(file)

    def config(self, section: str) -> Callable[[T], T]:
        def decor(cls: T) -> T:
            self.set_attrs(cls, self._cfg[section], cls)

            return cls

        return decor

    def list_config(self, section: str) -> Callable[[T], List[T]]:
        def decor(cls: T) -> List[T]:
            ls = []

            for item in self._cfg[section]:
                itm = cls()

                self.set_attrs(itm, item, cls)

                ls.append(itm)

            return ls

        return decor

    @staticmethod
    def set_attrs(target: object, source: Dict[str, Any], definition: object):
        try:
            for attr, type_ in definition.__annotations__.items():
                if typing.get_origin(type_) is Union:
                    types = [type__ for type__ in typing.get_args(type_) if type__ is not type(None)]

                    for try_, type__ in enumerate(types):
                        try:
                            setattr(target, attr, type__(source[attr]))
                            break
                        except KeyError:
                            setattr(target, attr, getattr(definition, attr, None))
                        except ValueError:
                            if try_ == len(types) - 1:
                                raise
                if typing.get_origin(type_) is list:
                    ls = []
                    type__ = typing.get_args(type_)[0]

                    for item in source[attr]:
                        ls.append(type__(item))

                    setattr(target, attr, ls)
                else:
                    setattr(target, attr, type_(source[attr]))
        except KeyError as err:
            raise InvalidConfigError(f"Could not create config due to missing keys") from err
        except ValueError as err:
            raise InvalidConfigError(f"Could not create config due to mismatched types") from err
