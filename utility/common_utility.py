"""
Module: utility.common_utility
Description: Core LLM interaction, prompt handling, and code verification logic.

This module provides asynchronous functions for:
- Pulling Ollama model instances
- Sending prompts to the LLM and retrieving responses
- Generating Python code for image creation
- Verifying generated code against specifications
"""

import re
import json
import logging
import traceback
import asyncio
from typing import Dict, List, Optional, Tuple

import aiohttp
from ollama import AsyncClient, pull

from .config_loader import get_config
from .code_execution_utility import execute_code

logger = logging.getLogger(__name__)

# Compiled regex pattern for extracting Python code blocks
PYTHON_CODE_RE_PATTERN = re.compile(r'```python\n(.*?)```', re.DOTALL)


async def pull_model_instance() -> Optional[bool]:
    """
    Pull the Ollama model instance with progress tracking.
    
    Attempts to pull the model specified in configuration. Monitors progress
    and logs status updates. Returns False if an exception occurs.
    
    Returns:
        Optional[bool]: False if an exception occurs, None on success (implicit)
    """
    config = get_config()
    oLLaMa_model = config.get('ollama.llm_model', 'llama3.1')
    stream_flag = config.get('ollama.model_specs.stream_flag', True)
    
    try:
        image_pull_response = pull(oLLaMa_model, stream=stream_flag)
        progress_states: set = set()
        
        logger.info(f"pull_model_instance : Instantiating '{oLLaMa_model}' model...")
        
        for progress in image_pull_response:
            status = progress.get("status")
            
            if status in progress_states:
                continue
            
            progress_states.add(status)
            logger.info(f"pull_model_instance : '{oLLaMa_model}' Model Fetching Status : {status}")
        
        return None
        
    except aiohttp.ClientError as exc:
        error_msg = f"pull_model_instance : Exception occurred while pulling model instance: {exc}"
        logger.error(error_msg)
        return False
    except Exception as exc:
        error_msg = f"pull_model_instance : Unexpected error: {exc}"
        logger.error(error_msg)
        logger.error(f"pull_model_instance : Traceback : {traceback.format_exc()}")
        return False


async def get_prompt_response(input_prompt: Optional[str] = None) -> Optional[str]:
    """
    Send a user-provided prompt to a chat model and retrieve the response.
    
    Args:
        input_prompt: The prompt to be sent to the chat model. Defaults to None.
        
    Returns:
        Optional[str]: The content of the chat model's response with surrounding
                      quotes stripped, or None if an error occurs.
    """
    config = get_config()
    oLLaMa_model = config.get('ollama.llm_model', 'llama3.1')
    user_role = config.get('ollama.model_specs.role', 'user')
    timeout = config.get('ollama.timeouts.chat_request', 60)
    
    try:
        logger.info("get_prompt_response : Execution Start")
        
        if input_prompt is None:
            logger.warning("get_prompt_response : No input prompt provided")
            return None
        
        logger.debug(f"get_prompt_response : Prompt : {input_prompt}")
        
        chat_response = await AsyncClient().chat(
            oLLaMa_model,
            messages=[{'role': user_role, 'content': input_prompt}]
        )
        chat_response = chat_response['message']['content'].strip('"')
        
        logger.info(f"get_prompt_response : Ollama's '{oLLaMa_model}' LLM Model Response : {chat_response}")
        
        logger.info("get_prompt_response : Execution End")
        return chat_response
        
    except asyncio.TimeoutError:
        error_msg = f"get_prompt_response : Timeout after {timeout}s"
        logger.error(error_msg)
        return None
    except Exception as exc:
        error_msg = f"get_prompt_response : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"get_prompt_response : Traceback : {traceback.format_exc()}")
        return None


async def filter_code_response(chat_response: str) -> Optional[str]:
    """
    Extract Python code block from LLM chat response.
    
    Args:
        chat_response: The raw response from the LLM containing potential code blocks.
        
    Returns:
        Optional[str]: Extracted Python code block, or message if no code found,
                      or None if an error occurs.
    """
    config = get_config()
    oLLaMa_model = config.get('ollama.llm_model', 'llama3.1')
    
    try:
        logger.info("filter_code_response : Execution Start")
        
        python_code_re_pattern_match = PYTHON_CODE_RE_PATTERN.search(chat_response)
        
        if python_code_re_pattern_match:
            python_code_block = python_code_re_pattern_match.group(1).strip()
            logger.info("filter_code_response : Python code block extracted successfully")
            logger.info("filter_code_response : Execution End")
            return python_code_block
        else:
            logger.warning("filter_code_response : No code block found in response")
            logger.info("filter_code_response : Execution End")
            return f" \nNo Code Block Found in {oLLaMa_model} response !\n"
            
    except Exception as exc:
        error_msg = f"filter_code_response : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"filter_code_response : Traceback : {traceback.format_exc()}")
        return None


async def get_prompt_context_response(
    input_specifications: Dict[str, str],
    reverification_flag: bool = False,
    python_code: Optional[str] = None
) -> Optional[str]:
    """
    Generate Python code for image creation based on specifications.
    
    Args:
        input_specifications: Dictionary containing dimension, shape, color, area.
        reverification_flag: If True, generates rectification prompt; if False, generates initial code.
        python_code: Existing code to rectify (required if reverification_flag is True).
        
    Returns:
        Optional[str]: Generated Python code block, or None if an error occurs.
    """
    config = get_config()
    oLLaMa_model = config.get('ollama.llm_model', 'llama3.1')
    timeout = config.get('ollama.timeouts.generate_request', 120)
    
    verification_config = config.get('verification', {})
    rectification_template = verification_config.get(
        'rectification_template',
        "Need to rectify python code: {code} because it was not satisfying my criteria which is to draw a {dimension} {shape} with a {color} color {area} it's boundary area. Please include the necessary libraries and ensure the {shape} is rendered correctly in {dimension} with the specified colored area. Don't forget to save plotted image"
    )
    
    try:
        logger.info("get_prompt_context_response : Execution Start")
        
        dimension = input_specifications.get('dimension', '2D')
        shape = input_specifications.get('shape', 'circle')
        color = input_specifications.get('color', 'blue')
        area = input_specifications.get('area', 'Inside')
        
        if reverification_flag and python_code:
            input_context = rectification_template.format(
                code=python_code,
                dimension=dimension,
                shape=shape,
                color=color,
                area=area
            )
        else:
            input_context = (
                f"I want to write Python code to draw a {dimension} {shape} with a {color} color "
                f"{area} it's boundary area. Please include the necessary libraries and ensure the "
                f"{shape} is rendered correctly in {dimension} with the specified colored area. "
                f"Also want to save plotted image as well"
            )
        
        logger.debug(f"get_prompt_context_response : Code Generation Prompt : {input_context}")
        logger.info(f"get_prompt_context_response: '{oLLaMa_model}' is generating code...")
        
        chat_response = await AsyncClient().generate(oLLaMa_model, prompt=input_context)
        chat_response = chat_response['response']
        
        logger.info("get_prompt_context_response : Execution End")
        
        return await filter_code_response(chat_response)
        
    except asyncio.TimeoutError:
        error_msg = f"get_prompt_context_response : Timeout after {timeout}s"
        logger.error(error_msg)
        return None
    except Exception as exc:
        error_msg = f"get_prompt_context_response : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"get_prompt_context_response : Traceback : {traceback.format_exc()}")
        return None


async def code_verification(
    python_code: str,
    prompt_specification_dict: Dict[str, str],
    current_attempt: int = 1
) -> bool:
    """
    Verify generated Python code against specifications.
    
    Sends code to LLM for verification and executes it. If verification fails
    or execution fails, recursively attempts to rectify the code up to max attempts.
    
    Args:
        python_code: The Python code to verify.
        prompt_specification_dict: Dictionary containing dimension, shape, color, area.
        current_attempt: Current verification attempt number (for recursion limit).
        
    Returns:
        bool: True if code passes verification and execution, False otherwise.
    """
    config = get_config()
    oLLaMa_model = config.get('ollama.llm_model', 'llama3.1')
    max_attempts = config.get('ollama.retries.verification_max_attempts', 3)
    
    verification_config = config.get('verification', {})
    prompt_template = verification_config.get(
        'prompt_template',
        "Please verify the following Python code: '{code}'. Does it meet all the specifications? mentioned - Dimension: {dimension}, Shape: {shape}, Color: {color}. Which were colored {area} boundry area of {shape}. NOTE: Just return 'True' if the code is perfect and error-free; otherwise, return 'False'. So, return only one word answer."
    )
    
    try:
        logger.info("code_verification : Execution Start")
        
        if current_attempt > max_attempts:
            logger.error(f"code_verification : Max attempts ({max_attempts}) reached. Stopping verification.")
            return False
        
        logger.info(f"code_verification : Feeding code to '{oLLaMa_model}' for verification...")
        
        dimension = prompt_specification_dict.get('dimension', '2D')
        shape = prompt_specification_dict.get('shape', 'circle')
        color = prompt_specification_dict.get('color', 'blue')
        area = prompt_specification_dict.get('area', 'Inside')
        
        verification_prompt = prompt_template.format(
            code=python_code,
            dimension=dimension,
            shape=shape,
            color=color,
            area=area
        )
        
        verification_response = await get_prompt_response(input_prompt=verification_prompt)
        
        if verification_response is None:
            logger.warning("code_verification : No verification response received")
            verification_flag = False
        else:
            verification_response = verification_response.replace('.', '').replace('!', '').strip()
            verification_flag = _strtobool(verification_response)
        
        execution_flag = await execute_code()
        
        if verification_flag is False or execution_flag is False:
            logger.warning(f"code_verification : '{oLLaMa_model}' Feedback : Verification Flag : {verification_flag}")
            logger.info(f"code_verification : '{oLLaMa_model}' is regenerating better version of code again")
            
            python_code = await get_prompt_context_response(
                input_specifications=prompt_specification_dict,
                reverification_flag=True,
                python_code=python_code
            )
            
            if python_code is None:
                logger.error("code_verification : Failed to generate rectified code")
                return False
            
            verification_flag = await code_verification(
                python_code,
                prompt_specification_dict,
                current_attempt + 1
            )
        
        logger.info(f"code_verification : '{oLLaMa_model}' Completed code verification process")
        logger.info("code_verification : Execution End")
        return verification_flag
        
    except Exception as exc:
        error_msg = f"code_verification : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"code_verification : Traceback : {traceback.format_exc()}")
        return False


def _strtobool(val: str) -> bool:
    """
    Convert a string representation of truth to boolean.
    
    Custom implementation to avoid deprecated distutils.util.strtobool.
    
    Args:
        val: String value to convert ('true', 'false', 'yes', 'no', '1', '0', etc.)
        
    Returns:
        bool: True for truthy values, False for falsy values.
        
    Raises:
        ValueError: If the value is not a valid truth string.
    """
    val = val.lower().strip()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        logger.warning(f"_strtobool : Invalid truth value: {val}, defaulting to False")
        return False


async def initiate_image_process() -> Optional[Tuple[str, Dict[str, str]]]:
    """
    Initiate the image generation process.
    
    Fetches image specifications (dimension, shape, color, area) from the LLM,
    then generates Python code to create the image.
    
    Returns:
        Optional[Tuple[str, Dict[str, str]]]: Tuple of (python_code_block, prompt_response_dict),
                                              or None if an error occurs.
    """
    config = get_config()
    prompt_config_path = config.get('prompt_config_path', './config/prompt_config.json')
    
    try:
        logger.info("initiate_image_process : Execution Start")
        
        prompt_config_dict = _load_prompt_config(prompt_config_path)
        prompts = prompt_config_dict.get('prompts', {})
        
        prompt_response_dict: Dict[str, str] = {}
        
        for key, prompt_text in prompts.items():
            chat_response = await get_prompt_response(input_prompt=prompt_text)
            if chat_response:
                prompt_response_dict[key] = chat_response
            else:
                logger.warning(f"initiate_image_process : No response for prompt '{key}', using default")
                prompt_response_dict[key] = _get_default_spec(key)
        
        logger.info(f"initiate_image_process : Specifications: {prompt_response_dict}")
        
        python_code_block = await get_prompt_context_response(input_specifications=prompt_response_dict)
        
        logger.info("initiate_image_process : Execution End")
        return python_code_block, prompt_response_dict
        
    except Exception as exc:
        error_msg = f"initiate_image_process : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"initiate_image_process : Traceback : {traceback.format_exc()}")
        return None


def _load_prompt_config(config_path: str) -> Dict:
    """
    Load prompt configuration from JSON file.
    
    Args:
        config_path: Path to the prompt configuration JSON file.
        
    Returns:
        Dict: Prompt configuration dictionary.
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"_load_prompt_config : Config file not found: {config_path}")
        return {'prompts': {}}
    except json.JSONDecodeError as e:
        logger.error(f"_load_prompt_config : Invalid JSON in config file: {e}")
        return {'prompts': {}}


def _get_default_spec(key: str) -> str:
    """
    Get default specification value for a given key.
    
    Args:
        key: Specification key (dimension, shape, color, area).
        
    Returns:
        str: Default value for the specification.
    """
    defaults = {
        'dimension': '2D',
        'shape': 'circle',
        'color': 'blue',
        'area': 'Inside'
    }
    return defaults.get(key, '2D')
