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
import json
from collections import abc
from functools import partial
from pathlib import Path
from typing import Callable, Iterator, IO, List, Optional, TypeVar, Union, Mapping, MutableMapping, Dict

try:
    import yaml
except ImportError as _yaml_exception:
    _yaml_imported = False
else:
    _yaml_imported = True

ParsedValue = Union[str, int, List["ParsedValue"], "ParsedFile"]
ParsedFile = MutableMapping[str, ParsedValue]

CustomLoaders = Dict[str, Callable[[IO[str]], ParsedFile]]


class UnknownFileType(Exception):
    pass


KT = TypeVar("KT")
VT = TypeVar("VT")


def create_ignore_tag(tag: str):
    def ignore_tag(loader, node):
        if node.id == 'scalar':
            return f"{tag} {loader.construct_scalar(node)}"
        else:
            return f"{tag} {' '.join(loader.construct_sequence(node))}"

    return ignore_tag


class Loader(abc.Mapping, Mapping[str, ParsedValue]):

    def load_file(self, path: Path) -> ParsedFile:
        try:
            with open(path, encoding="UTF-8") as file:
                return self._loaders[path.suffix](file)
        except KeyError:
            if path.suffix in [".yml", ".yaml"]:
                raise ImportError("PyYAML is required to do this, please use the yaml extra") from _yaml_exception
            else:
                raise UnknownFileType(f"Cannot parse files with the {path.suffix} extension") from None

    def check_include_string(self, sequence: list) -> bool:
        if self._include_default_string is None:
            return False

        if isinstance(self._include_default_string, str):
            if self._include_default_string in sequence:
                sequence.remove(self._include_default_string)
                return True
            else:
                return False

        result = False
        for string in self._include_default_string:
            if string in sequence:
                sequence.remove(string)
                result = True

        return result

    def recursive_update(
        self,
        original: MutableMapping[KT, VT],
        update: MutableMapping[KT, VT]
    ) -> None:
        for key, value in update.items():
            if key in original:
                original_value = original[key]
                if isinstance(original_value, dict):
                    self.recursive_update(original_value, value)
                elif (
                    isinstance(original_value, list)
                    and self.check_include_string(original_value)
                ):
                    original_value.extend(value)
                else:
                    original[key] = value
            else:
                original[key] = value

    def __init_yaml(self, env_tag: str):
        if _yaml_imported:
            class YamlLoader(yaml.SafeLoader):
                yaml_constructors = yaml.SafeLoader.yaml_constructors.copy()

            YamlLoader.add_constructor(env_tag, create_ignore_tag(env_tag))

            self._loaders[".yml"] = self._loaders[".yaml"] = partial(yaml.load, Loader=YamlLoader)

    def __init__(
        self,
        config: Union[str, Path],
        *config_files: Union[str, Path],
        include_default_string: Optional[Union[str, List[str]]] = None,
        env_tag: Optional[str] = "!ENV",
        custom_file_loaders: Optional[CustomLoaders] = None
    ) -> None:
        self._include_default_string = include_default_string
        self._loaders: CustomLoaders = {
            ".json": json.load
        }

        self.__init_yaml(env_tag)

        # add the custom loaders
        if custom_file_loaders:
            self._loaders.update(custom_file_loaders)

        # finally, load the file
        self._data = self.load_file(Path(config))
        for file in config_files:
            self.recursive_update(
                self._data,
                self.load_file(Path(file))
            )

    def __getitem__(self, k: str) -> ParsedValue:
        return self._data[k]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[ParsedValue]:
        return iter(self._data)

    def __str__(self) -> str:
        return str(self._data)
