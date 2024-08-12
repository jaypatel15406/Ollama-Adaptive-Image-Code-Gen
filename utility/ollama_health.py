#* Import all the important modules
import aiohttp, logging, traceback
from .common_utility import config_dict

#* Unpack configurational values
host = config_dict['host']
port = config_dict['port']

async def check_service_running(host='localhost', port=11434):
    '''
    Description:
    ============
        This asynchronous function checks whether a service is running and accessible
        at a specified host and port by sending an HTTP GET request. It determines
        if the service is up by verifying if the HTTP response status code indicates
        success (200-299).

    Parameters:
    ============
        host (`str`) : The host where the service is running. Default is 'localhost'.
        port (`int`) : The port on which the service is running. Default is 11434.

    Returns:
    ============
        bool : True if the service responds with a status code in the 200-299 range,
                indicating that the service is running; otherwise, False.
    '''
    url = f'http://{host}:{port}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Check if the response status is OK (200-299)
                if response.status in range(200, 300):
                    return True
                else:
                    logging.debug(f" ollama_health : check_service_running : Received status code {response.status} from {url}")
                    return False
    except aiohttp.ClientError as exe:
        logging.error(f" ollama_health : check_service_running : Client error occurred: {exe}")
        return False

async def check_ollama_health():
    '''
    Description:
    ============
        This asynchronous function calls `check_service_running` with default parameters
        to check if the service is running on 'localhost' at port 11434. Based on the
        result, it logs whether the service is running or not.

    Returns:
    ============
        health_flag (`bool`) : True if the service responds with a status code in the 200-299 range,
                indicating that the service is running; otherwise, False.
    '''
    logging.info(" ollama_health : check_ollama_health : Execution Start")
    logging.info("Started Checking OLLaMa Service Health ...")
    if await check_service_running(host, port):
        logging.info(f" ollama_health : check_ollama_health : Service is running on {host}:{port}")
        flag = True
    else:
        logging.error(f" ollama_health : check_ollama_health : Service is not running on {host}:{port}")
        flag = False
    health_flag = flag
    logging.info(" ollama_health : check_ollama_health : Execution End")
    return health_flag
