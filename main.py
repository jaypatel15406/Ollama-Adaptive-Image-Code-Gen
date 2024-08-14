# Import all the important modules
import os
import logging
import traceback
import asyncio
from utility.ollama_health import check_ollama_health
from utility.common_utility import initiate_image_process, pull_model_instance, code_verification, config_dict

#* Unpack all necessary 'parameters' from 'config_dict'
generated_code_config_dict = config_dict['generated_code_config']

async def get_ollama_response():
    '''
    Description:
    ============
        This asynchronous function retrieves a response from the 'OLLaMa Model' for preparing
        an image using 'Python Programming' language.

    Returns:
    ============
        python_code (`str`) : Python code [i.e., `response` sent by 'OLLaMa Model']
    '''
    try:
        logging.info("main : get_ollama_response : Execution Start")
        python_code, prompt_specification_dict = await initiate_image_process()
        
        file_path = os.path.join(generated_code_config_dict['dir_path'], generated_code_config_dict['file_path'])
        print(f" main : get_ollama_response : Python Code Generated Successfully. Initiating Process to storing it under : {file_path} DIR")

        # Create the directory if it doesn't exist
        os.makedirs(generated_code_config_dict['dir_path'], exist_ok=True)

        # Write the code string to the file
        with open(file_path, 'w') as file: file.write(python_code)

        flag = await code_verification(python_code, prompt_specification_dict)
        
        logging.info(" main : get_ollama_response : Execution End")
        return flag
    except Exception as exc:
        logging.error(f" main : get_ollama_response : Error : {exc}")
        logging.error(f" main : get_ollama_response : Traceback : {traceback.format_exc()}")
        return None

async def main():
    '''
    Description:
    ============
        Currently This asynchronous function checks the health of the 'OLLaMa' service and, if it's healthy,
        retrieves a response from the 'OLLaMa Model'. Logs an error and terminates if the service is not healthy.

    Returns:
    ============
        None
    '''
    try:
        # Check whether 'OLLaMa' is serving or not. If it's serving, continue the program; otherwise, log an error
        health_flag = await check_ollama_health()

        if health_flag:
            await pull_model_instance()
            response = await get_ollama_response()
            if response:
                print(f"Received response, and Code generated successfully ...")
            else:
                print(f"Issue while generating response")
        else:
            logging.error(" OLLaMa Service Health Check Failed. Stopping Application due to 'Bad Health' ...")

    except Exception as exc:
        logging.error(f" main : Error : {exc}")
        logging.error(f" main : Traceback : {traceback.format_exc()}")

# Run the async main function
if __name__ == '__main__':
    asyncio.run(main())
