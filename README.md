# Yaml Config

This is a small module you can use to use yaml config files

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
from yaml_config import Config

config = Config("path/to/config.yaml")

@config.config("general")
class General:
    name: str
    frequency: int

@config.list_config("targets")
class Targets:
    name: str
    size: str

print(General.name)

for target in Targets:
    print(target.name)
```
