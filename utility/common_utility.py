#* Import all the important modules
import json

#* Initialization of 'config' paths
config_json_path = "./config/config.json"
prompt_config_json_path = "./config/prompt_config.json"

#* Open 'config' files
with open(config_json_path, 'r') as file_path: config_dict = json.load(file_path)
with open(prompt_config_json_path, 'r') as file_path: prompt_config_dict = json.load(file_path)