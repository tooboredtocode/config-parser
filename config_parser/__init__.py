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
from pathlib import Path
from typing import Callable, List, Optional, Union, TypeVar

from .loader import CustomLoaders, Loader, ParsedFile
from .parser import Parser

T = TypeVar("T")


def load_config(
    config: Union[str, Path],
    *config_files: Union[str, Path],
    include_default_string: Optional[Union[str, List[str]]] = None,
    env_tag: Optional[str] = "!ENV",
    custom_file_loaders: Optional[CustomLoaders] = None
) -> Callable[[T], T]:
    """
    Loads the config from one or more files and provides decorators to populate classes with the values
    :param config: The initial config to load
    :param config_files: A list of config files which will be used to recursively update the original dictionary
    :param include_default_string: If specified, lists will no longer be replaced but updated if one of the
    specified strings is found
    :param env_tag: default: !ENV
    :param custom_file_loaders: A dictionary of file suffixes (prefixed with .) with a function that can load a file
    type into a dictionary
    """

    data = Loader(
        config,
        *config_files,
        include_default_string=include_default_string,
        env_tag=env_tag,
        custom_file_loaders=custom_file_loaders
    )

    return Parser(data, env_tag).create_config
