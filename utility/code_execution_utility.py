#* Import all Important Modules
import os
import ast
import sys
import json
import logging
import traceback
import subprocess

# Initialization of 'config' paths
config_json_path = "./config/config.json"

# Open 'config' files
with open(config_json_path, 'r') as file_path:
    config_dict = json.load(file_path)

# Global Path of 'Python Code' unpacked from 'config_dict'
generated_code_config_dict = config_dict['generated_code_config']
oLLaMa_generated_code_path = os.path.join(generated_code_config_dict['dir_path'], generated_code_config_dict['file_path'])

def get_imports(script_path):
    with open(script_path, "r") as file:
        tree = ast.parse(file.read(), filename=script_path)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module.split('.')[0])
    return modules

def install_modules(modules):
    for module in modules:
        try:
            print(f" utility : install_modules : Installing module: {module}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
        except subprocess.CalledProcessError as e:
            logging.error(f" utility : install_modules : Failed to install {module}: {e}")
        except Exception as e:
            logging.error(f" utility : install_modules : Unexpected error occurred while installing {module}: {e}")

async def execute_code():
    try:
        print("\n=========================================================================================\n")
        logging.info(" utility : execute_code : Execution Start")

        #* Fetch Import and Install it
        modules = get_imports(oLLaMa_generated_code_path)
        install_modules(modules)

        #* Read 'Generated Python Code' and Execute the same
        with open(oLLaMa_generated_code_path, 'r') as generated_file_path: generated_python_code = generated_file_path.read()
        exec(generated_python_code)

        logging.info(" utility : execute_code : Execution End")
        print("\n=========================================================================================\n")
        return True

    except Exception as exc:
        logging.error(f" utility : execute_code : Error: {exc}")
        logging.error(f" utility : execute_code : Traceback: {traceback.format_exc()}")
        return False