from .create_config import save_config_to_file, create_config_from_json, config_to_json
from .default_config2 import default_config
import json


print(default_config.to_json())

# save_config_to_file(default_config, 'default_config3.json')

json_data = config_to_json(default_config)
print(json_data)
print(json.dumps(json_data, indent=4))

config = create_config_from_json(json_data)
print(config.to_json())
