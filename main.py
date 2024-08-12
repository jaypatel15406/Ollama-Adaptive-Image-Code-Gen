# Import all the important modules
import ollama
import logging
import traceback
import asyncio
from utility.ollama_health import check_ollama_health
from utility.common_utility import initiate_image_process, pull_model_instance

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
        
        #TODO Commented 'While True' for single instance test
        # while True
        #     python_code = await initiate_image_process()
        python_code = await initiate_image_process()

        logging.info("main : get_ollama_response : Execution End")
        return python_code  # Placeholder for actual response

    except Exception as exc:
        logging.error(f"main : get_ollama_response : Error : {exc}")
        logging.error(f"main : get_ollama_response : Traceback : {traceback.format_exc()}")
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
                print(f"Received response: {response}")
        else:
            logging.error(" OLLaMa Service Health Check Failed. Stopping Application due to 'Bad Health' ...")

    except Exception as exc:
        logging.error(f" main : Error : {exc}")
        logging.error(f" main : Traceback : {traceback.format_exc()}")

# Run the async main function
if __name__ == '__main__':
    asyncio.run(main())
