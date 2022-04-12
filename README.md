# Bored Config Parser

This is a small module you can use to make using config files easy

### Example

A config like this:
```yaml
general:
  name: "test"
  frequency: 22

targets:
  - name: "t1"
    size: "2G"
  - name: "t2"
    size: "1G"
```

can be easily used with the following code:
```python
from typing import List

from config_parser import load_config


class General:
    name: str
    frequency: int


class Target:
    name: str
    size: str

    
@load_config("path/to/config.yaml")
class Config:
    general: General
    targets: List[Target]


print(Config.general.name)

for target in Config.targets:
    print(target.name)
```
