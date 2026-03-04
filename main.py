"""
Module: main
Description: Ollama Adaptive Image Code Gen - Main Application Entry Point

This application uses Ollama LLM to:
1. Choose image specifications (dimension, shape, color, area)
2. Generate Python code for drawing the image
3. Execute code with automatic dependency installation
4. Verify generated code against specifications
5. Iteratively rectify code if verification fails
"""

import os
import sys
import logging
import traceback
import asyncio
import signal
from typing import Optional

from utility.ollama_health import check_ollama_health
from utility.common_utility import initiate_image_process, pull_model_instance, code_verification
from utility.config_loader import get_config, print_startup_banner
from utility.version import __version__

# Configure logging
def setup_logging() -> None:
    """Configure logging with format and level from configuration."""
    config = get_config()
    
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = config.get('logging.file', 'logs/app.log')
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"setup_logging : Logging configured with level={log_level}, file={log_file}")


async def get_ollama_response() -> Optional[bool]:
    """
    Retrieve response from Ollama Model for image generation.
    
    This asynchronous function:
    1. Initiates image process to get specifications and generated code
    2. Saves the generated code to the configured directory
    3. Performs code verification
    
    Returns:
        Optional[bool]: True if code generation and verification successful,
                       False otherwise, None on error.
    """
    logger = logging.getLogger(__name__)
    config = get_config()
    
    generated_code_config = config.get('generated_code_config', {})
    dir_path = generated_code_config.get('dir_path', 'oLLaMa_generated_code_dir')
    file_path = generated_code_config.get('file_path', 'generated_code.py')
    
    try:
        logger.info("get_ollama_response : Execution Start")
        
        python_code, prompt_specification_dict = await initiate_image_process()
        
        if python_code is None:
            logger.error("get_ollama_response : Failed to generate Python code")
            print(" main : get_ollama_response : Failed to generate Python code")
            logger.info("get_ollama_response : Execution End")
            return None
        
        full_path = os.path.join(dir_path, file_path)
        
        # Create the directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        
        # Write the code string to the file
        with open(full_path, 'w') as file:
            file.write(python_code)
        
        print(f" main : get_ollama_response : Python Code Generated Successfully. Saved to: {full_path}")
        logger.info(f"get_ollama_response : Python code saved to {full_path}")
        
        # Perform code verification
        verification_flag = await code_verification(python_code, prompt_specification_dict)
        
        logger.info("get_ollama_response : Execution End")
        return verification_flag
        
    except Exception as exc:
        error_msg = f"get_ollama_response : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"get_ollama_response : Traceback : {traceback.format_exc()}")
        return None


async def main() -> None:
    """
    Main application entry point.
    
    This asynchronous function:
    1. Checks Ollama service health
    2. Pulls the required model instance
    3. Retrieves response and generates code
    4. Handles graceful shutdown on signals
    
    Returns:
        None
    """
    logger = logging.getLogger(__name__)
    config = get_config()
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig: signal.Signals) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"main : Received shutdown signal: {sig.name}")
        print(f"\n main : Received shutdown signal ({sig.name}), cleaning up...")
        shutdown_event.set()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
        except NotImplementedError:
            # Signal handlers not supported on this platform (e.g., Windows)
            logger.warning(f"main : Signal handler for {sig.name} not supported on this platform")
    
    try:
        # Check Ollama service health
        print("\n[Step 1/3] Checking Ollama service health...")
        health_flag = await check_ollama_health()
        
        if not health_flag:
            logger.error("main : Ollama Service Health Check Failed. Stopping Application due to 'Bad Health'")
            print("\n[ERROR] Ollama Service Health Check Failed. Stopping Application due to 'Bad Health' ...")
            return
        
        print("[OK] Ollama service is healthy\n")
        
        # Pull model instance
        print("[Step 2/3] Pulling model instance...")
        model_name = config.get('ollama.llm_model', 'llama3.1')
        await pull_model_instance()
        print(f"[OK] Model '{model_name}' is ready\n")
        
        # Get response and generate code
        print("[Step 3/3] Generating and verifying code...")
        response = await get_ollama_response()
        
        if response:
            print("\n[OK] Application completed successfully - Code generated and verified!")
            logger.info("main : Application completed successfully")
        elif response is False:
            print("\n[WARNING] Code verification failed after maximum attempts")
            logger.warning("main : Code verification failed after maximum attempts")
        else:
            print("\n[ERROR] Issue while generating response")
            logger.error("main : Issue while generating response")
        
    except asyncio.CancelledError:
        logger.info("main : Application shutdown cancelled")
        print("\n[INFO] Application shutdown in progress...")
    except Exception as exc:
        error_msg = f"main : Error : {exc}"
        logger.error(error_msg)
        logger.error(f"main : Traceback : {traceback.format_exc()}")
        print(f"\n[ERROR] Unexpected error: {exc}")
    finally:
        logger.info("main : Application shutting down...")


def main_entry() -> None:
    """
    Synchronous entry point that sets up logging and runs the async main.
    
    This wrapper function:
    1. Prints startup banner with configuration
    2. Sets up logging configuration
    3. Runs the async main function
    """
    # Print startup banner FIRST (before logging setup)
    print_startup_banner()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"main_entry : Ollama Adaptive Image Code Gen v{__version__} starting...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("main_entry : Application interrupted by user")
        print("\n[INTERRUPTED] Application interrupted by user")
    except Exception as exc:
        error_msg = f"main_entry : Fatal error: {exc}"
        logger.error(error_msg)
        logger.error(f"main_entry : Traceback : {traceback.format_exc()}")
        print(f"\n[FATAL ERROR] Application failed: {exc}")
        print("\nApplication failed to start. Check logs/app.log for details.")
        sys.exit(1)


if __name__ == '__main__':
    main_entry()
