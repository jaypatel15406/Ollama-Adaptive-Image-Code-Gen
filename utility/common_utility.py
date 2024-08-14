#* Import all the important modules
import re
import json
import logging
import traceback
import aiohttp, logging, traceback
from ollama import AsyncClient, pull
from distutils.util import strtobool
from .code_execution_utility import execute_code

#* Initialization of 'config' paths
config_json_path = "./config/config.json"
prompt_config_json_path = "./config/prompt_config.json"

#* Open 'config' files
with open(config_json_path, 'r') as file_path: config_dict = json.load(file_path)
with open(prompt_config_json_path, 'r') as file_path: prompt_config_dict = json.load(file_path)

#* Unpack configurational values
oLLaMa_model = config_dict['llm_model']
stream_flag = config_dict['model_specs']['stream_flag']
user_role = config_dict['model_specs']['role']

#* Initialization of 'Global Variables'
PYTHON_CODE_RE_PATTERN = re.compile(r'```python\n(.*?)```', re.DOTALL)

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
        # Initiates the image pulling process from the oLLaMa_model source
        image_pull_response = pull(oLLaMa_model, stream=stream_flag)
        progress_states = set()
        print(f" utility : pull_model_instance : Instansiating '{oLLaMa_model}' ... ")

        # Iterates through the progress updates of the image pull operation
        for progress in image_pull_response:
            # Skips progress updates if the status is already processed
            if progress.get("status") in progress_states:
                continue
            
            # Adds the current status to the set of processed statuses
            progress_states.add(progress.get("status"))
            
            # Logs the current status of the image pull process
            print(f" utility : pull_model_instance : '{oLLaMa_model}' Model Fetching Status : {progress.get('status')}")
    
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
        chat_response = await AsyncClient().chat(oLLaMa_model, messages=[{'role': user_role, 'content': input_prompt}])
        chat_response = chat_response['message']['content'].strip('"')
        
        print(f" utility : get_prompt_response : Ollama's '{oLLaMa_model}' LLM Model Response : {chat_response}")
        print("\n=========================================================================================\n")
        
        logging.info(" utility : get_prompt_response : Execution End")
        return chat_response
        
    except Exception as exc:
        logging.error(f" utility : get_prompt_response : Error : {exc}")
        logging.error(f" utility : get_prompt_response : Traceback : {traceback.format_exc()}")
        return None

async def filter_code_response(chat_response):
    try:
        logging.info(" utility : filter_code_response : Execution Start")
        python_code_re_pattern_match = PYTHON_CODE_RE_PATTERN.search(chat_response)
        if python_code_re_pattern_match:
            python_code_block = python_code_re_pattern_match.group(1).strip()
            logging.info(" utility : filter_code_response : Execution End")
            return python_code_block
        else:
            logging.info(" utility : filter_code_response : Execution End")
            return f" \nNo Code Block Found in {oLLaMa_model} response !\n"
    except Exception as exc:
        logging.error(f" utility : filter_code_response : Error : {exc}")
        logging.error(f" utility : filter_code_response : Traceback : {traceback.format_exc()}")
        return None

async def get_prompt_context_response(input_specifications= {}, reverification_flag= False, python_code= None) -> str:
    try:
        logging.info(" utility : get_prompt_context_response : Execution Start")
        
        #* Initialization of an 'input_context'
        if reverification_flag:
            input_context = f"Need to rectify python code: {python_code} because it was not satisfying my criteria which is to draw a {input_specifications['dimension']} {input_specifications['shape']} with a {input_specifications['color']} color {input_specifications['area']} it's boundary area. Please include the necessary libraries and ensure the {input_specifications['shape']} is rendered correctly in {input_specifications['dimension']} with the specified colored area. Don't forget to save plotted image"
        else:
            input_context = f"I want to write Python code to draw a {input_specifications['dimension']} {input_specifications['shape']} with a {input_specifications['color']} color {input_specifications['area']} it's boundary area. Please include the necessary libraries and ensure the {input_specifications['shape']} is rendered correctly in {input_specifications['dimension']} with the specified colored area. Also want to save plotted image as well"
        
        print(f" utility : get_prompt_context_response : Code Generation Prompt : {input_context}")
        print("\n=========================================================================================\n")
        
        print(f" utility: get_prompt_context_response: '{oLLaMa_model}' is generating code ...\n Please sit back and enjoy a cup of coffee while it completes its work.")
        
        # Send the prompt to the generate model and get the response
        chat_response = await AsyncClient().generate(oLLaMa_model, prompt=input_context)
        chat_response = chat_response['response']
        
        print("\n=========================================================================================\n")
        logging.info(" utility : get_prompt_context_response : Execution End")
        
        #* Filter out the 'Python Code' from the 'Generated Response'
        return await filter_code_response(chat_response)
        
    except Exception as exc:
        logging.error(f" utility : get_prompt_context_response : Error : {exc}")
        logging.error(f" utility : get_prompt_context_response : Traceback : {traceback.format_exc()}")
        return None

async def code_verification(python_code, prompt_specification_dict):
    try:
        logging.info(" utility : code_verification : Execution Start")
        print("\n=========================================================================================\n")
        print(f" utility : code_verification : Feeding code to'{oLLaMa_model}' for the code verification process ...")
        
        #* Verify Code is proper or not 'Flag Based' If 'True', then break else return 'modified_python_code_block'
        verification_prompt = f"Please verify the following Python code: '{python_code}'. Does it meet all the specifications? mentioned - Dimension: {prompt_specification_dict['dimension']}, Shape: {prompt_specification_dict['shape']}, Color: {prompt_specification_dict['color']}. Which were colored {prompt_specification_dict['area']} boundry area of {prompt_specification_dict['shape']}. NOTE: Just return 'True' if the code is perfect and error-free; otherwise, return 'False'. So, return only one word answer."
        verification_flag = await get_prompt_response(input_prompt=verification_prompt)
        verification_flag = verification_flag.replace('.','').replace('!','')
        verification_flag = bool(strtobool(verification_flag))
        
        #* Execute Code and take 
        execution_flag = await execute_code()
        
        #* Need to 'Rectify' code until it get's perfect
        if verification_flag is False or execution_flag is False:
            print("\n=========================================================================================\n")
            print(f" utility : code_verification : '{oLLaMa_model}' Feedback : Verification Flag : {verification_flag}")
            print(f" utility : code_verification : '{oLLaMa_model}' is regenerating better version of code again ")
            print("\n=========================================================================================\n")
            python_code = await get_prompt_context_response(input_specifications=prompt_specification_dict, reverification_flag=True, python_code= python_code)
            verification_flag = await code_verification(python_code, prompt_specification_dict)
        
        print(f" utility : code_verification :  '{oLLaMa_model}' Completed code verification process ...")
        print("\n=========================================================================================\n")
        logging.info(" utility : code_verification : Execution End")
        return verification_flag
        
    except Exception as exc:
        logging.error(f" utility : code_verification : Error : {exc}")
        logging.error(f" utility : code_verification : Traceback : {traceback.format_exc()}")
        return False

async def initiate_image_process():
    try:
        logging.info(" utility : initiate_image_process : Execution Start")
        
        #* Fetch all details based on given 'prompts' and store the 'Response' received from the prompt into 'prompt_response_dict'
        prompts = prompt_config_dict['prompts']
        prompt_response_dict = {}
        for key, _ in prompts.items():
            chat_response = await get_prompt_response(prompts[key])
            prompt_response_dict[key] = chat_response
        # print(f"\n utility : initiate_image_process : prompt_response_dict : {prompt_response_dict}\n")
        
        # #* Fetch Python Code using 'Main Context'
        python_code_block = await get_prompt_context_response(input_specifications= prompt_response_dict)
        
        logging.info(" utility : initiate_image_process : Execution End")
        return python_code_block, prompt_response_dict
        
    except Exception as exc:
        logging.error(f" utility : initiate_image_process : Error : {exc}")
        logging.error(f" utility : initiate_image_process : Traceback : {traceback.format_exc()}")
        return None