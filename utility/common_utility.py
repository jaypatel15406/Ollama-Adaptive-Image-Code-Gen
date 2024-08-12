#* Import all the important modules
import json
import logging
import traceback
import aiohttp, logging, traceback
from ollama import AsyncClient, pull

#* Initialization of 'config' paths
config_json_path = "./config/config.json"
prompt_config_json_path = "./config/prompt_config.json"

#* Open 'config' files
with open(config_json_path, 'r') as file_path: config_dict = json.load(file_path)
with open(prompt_config_json_path, 'r') as file_path: prompt_config_dict = json.load(file_path)

#* Unpack configurational values
LLaMa_model = config_dict['model_lst'][0]
stream_flag = config_dict['model_specs']['stream_flag']
user_role = config_dict['model_specs']['role']

async def pull_model_instance():
    """
    Description:
    ============
        This asynchronous function attempts to pull model images from a specified
        model source. It monitors the progress of the image pull operation and
        logs the status at various stages. If any errors occur during the operation,
        they are caught and logged.

    Parameters:
    ============
        None

    Returns:
    ============
        bool : Returns `False` if an exception occurs during the image pull process.
                In the absence of exceptions, the function completes without returning
                a value, which implicitly means a successful image pull operation.
    """
    try:
        # Initiates the image pulling process from the LLaMa_model source
        image_pull_response = pull(LLaMa_model, stream=stream_flag)
        progress_states = set()
        print(f" utility : pull_model_instance : Instansiating '{LLaMa_model}' ... ")

        # Iterates through the progress updates of the image pull operation
        for progress in image_pull_response:
            # Skips progress updates if the status is already processed
            if progress.get("status") in progress_states:
                continue
            
            # Adds the current status to the set of processed statuses
            progress_states.add(progress.get("status"))
            
            # Logs the current status of the image pull process
            print(f" utility : pull_model_instance : '{LLaMa_model}' Model Fetching Status : {progress.get('status')}")
    
    except aiohttp.ClientError as exe:
        # Logs an error message if an exception occurs during the image pull operation
        logging.error(f" utility : pull_model_instance : Exception Occurred while Pulling Model Instance: {exe}")

async def get_prompt_response(input_prompt= None) -> str:
    """
    Description:
    ============
        This asynchronous function sends a user-provided prompt to a chat model
        and retrieves the model's response. In case of any exceptions during the 
        execution, it logs the error and traceback.

    Parameters:
    ============
        input_prompt (`str` or `None`) : The prompt to be sent to the chat model.
                                        Defaults to `None`, in which case no prompt is sent.

    Returns:
    ============
        str : The content of the chat model's response after stripping any surrounding
                quotes. Returns `None` if an error occurs during the process.
    """
    try:
        logging.info(" utility : get_prompt_response : Execution Start")
        
        print("\n=========================================================================================\n")
        print(f" utility : get_prompt_response : Prompt : {input_prompt}")
        
        # Send the prompt to the chat model and get the response
        chat_response = await AsyncClient().chat(LLaMa_model, messages=[{'role': user_role, 'content': input_prompt}])
        chat_response = chat_response['message']['content'].strip('"')
        
        print(f" utility : get_prompt_response : Ollama LLaMa 3.1 8B Response : {chat_response}")
        print("\n=========================================================================================\n")
        
        logging.info(" utility : get_prompt_response : Execution End")
        return chat_response
        
    except Exception as exc:
        logging.error(f" utility : get_prompt_response : Error : {exc}")
        logging.error(f" utility : get_prompt_response : Traceback : {traceback.format_exc()}")
        return None

async def get_context_response(input_context= None, input_specifications= {}) -> str:
    try:
        logging.info(" utility : get_context_response : Execution Start")
        
        #* Initialization of an 'input_context'
        input_context = f"I want to write Python code to draw a {input_specifications['dimension']} {input_specifications['shape']} with a {input_specifications['color']} color {input_specifications['area']} it's border area. Please include the necessary libraries and ensure the {input_specifications['shape']} is rendered correctly in {input_specifications['dimension']} with the specified border."
        print(f"input_prompt : {input_context}")
        
        # Send the prompt to the generate model and get the response
        chat_response = await AsyncClient().chat(LLaMa_model, messages=[{'role': user_role, 'content': input_context}])
        print(f"chat_response : {chat_response['message']['content']}")
        
        logging.info(" utility : get_context_response : Execution End")
        return "chat_response"
        
    except Exception as exc:
        logging.error(f" utility : get_context_response : Error : {exc}")
        logging.error(f" utility : get_context_response : Traceback : {traceback.format_exc()}")
        return None

async def initiate_image_process():
    try:
        logging.info(" utility : initiate_image_process : Execution Start")
        
        #* Fetch all details based on given 'prompts' and store the 'Response' received from the prompt into 'prompt_response_dict'
        prompts = prompt_config_dict['prompts']
        prompt_response_dict = {}
        for key, _ in prompts.items():
            chat_response = await get_prompt_response(prompts[key])
            prompt_response_dict[key] = chat_response
        print(f"\n utility : initiate_image_process : prompt_response_dict : {prompt_response_dict}\n")
        
        #* Fetch Python Code using 'Main Context'
        python_code = await get_context_response(input_context= prompt_config_dict['context'], input_specifications= prompt_response_dict)
        
        logging.info(" utility : initiate_image_process : Execution End")
        return prompt_response_dict
        
    except Exception as exc:
        logging.error(f" utility : initiate_image_process : Error : {exc}")
        logging.error(f" utility : initiate_image_process : Traceback : {traceback.format_exc()}")
        return None