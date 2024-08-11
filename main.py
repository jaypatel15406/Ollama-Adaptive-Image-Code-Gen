# Import all the important modules
import ollama
import logging
import traceback
import asyncio
from utility import ollama_health
from utility.common_utility import config_dict, prompt_config_dict

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

        #TODO Replace this with actual asynchronous operations
        print('Code Started')

        # Simulate an asynchronous operation if necessary
        await asyncio.sleep(1)  # Simulate a delay

        logging.info("main : get_ollama_response : Execution End")
        return "response from OLLAMA"  # Placeholder for actual response

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
        health_flag = await ollama_health.check_ollama_health()  # Ensure this function is async

        if health_flag:
            response = await get_ollama_response()
            if response:
                print(f"Received response: {response}")
        else:
            logging.error("OLLaMa Service Health Check Failed. Stopping Application due to 'Bad Health' ...")

    except Exception as exc:
        logging.error(f"main : Error : {exc}")
        logging.error(f"main : Traceback : {traceback.format_exc()}")

# Run the async main function
if __name__ == '__main__':
    asyncio.run(main())
