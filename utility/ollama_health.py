"""
Module: utility.ollama_health
Description: Ollama service health checking and model readiness validation.

This module provides:
- Service availability checking via HTTP health endpoint
- Model readiness verification (not just server running)
- Retry logic with configurable attempts and intervals
"""

import logging
import traceback
import asyncio
from typing import Optional

import aiohttp

from .config_loader import get_config

logger = logging.getLogger(__name__)


async def check_service_running(host: str, port: int, timeout: int = 10) -> bool:
    """
    Check if Ollama service is running and accessible.
    
    Sends an HTTP GET request to the Ollama server and verifies
    the response status code indicates success (200-299).
    
    Args:
        host: The host where the service is running.
        port: The port on which the service is running.
        timeout: Request timeout in seconds.
        
    Returns:
        bool: True if the service responds with status 200-299, False otherwise.
    """
    url = f'http://{host}:{port}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if 200 <= response.status < 300:
                    logger.debug(f"check_service_running : Service responding at {url} with status {response.status}")
                    return True
                else:
                    logger.debug(f"check_service_running : Received status code {response.status} from {url}")
                    return False
                    
    except asyncio.TimeoutError:
        logger.error(f"check_service_running : Timeout connecting to {url} after {timeout}s")
        return False
    except aiohttp.ClientError as exc:
        logger.error(f"check_service_running : Client error occurred: {exc}")
        return False
    except Exception as exc:
        logger.error(f"check_service_running : Unexpected error: {exc}")
        logger.error(f"check_service_running : Traceback : {traceback.format_exc()}")
        return False


async def check_model_readiness(model_name: str, host: str, port: int) -> bool:
    """
    Check if a specific model is loaded and ready in Ollama.
    
    Queries the Ollama API to list available models and verifies
    the specified model is present.
    
    Args:
        model_name: Name of the model to check (e.g., 'llama3.1').
        host: The host where Ollama is running.
        port: The port on which Ollama is running.
        
    Returns:
        bool: True if the model is available, False otherwise.
    """
    from ollama import AsyncClient
    
    try:
        logger.info(f"check_model_readiness : Checking if model '{model_name}' is ready...")
        
        client = AsyncClient(host=f'http://{host}:{port}')
        response = await client.list()
        
        # Handle different response formats
        if isinstance(response, dict):
            models = response.get('models', [])
        elif hasattr(response, 'models'):
            models = response.models
        else:
            models = response or []
        
        logger.debug(f"check_model_readiness : Raw response: {response}")
        logger.debug(f"check_model_readiness : Parsed models: {models}")
        
        for model in models:
            # Handle both dict and object formats
            if isinstance(model, dict):
                model_name_value = model.get('name', '')
            else:
                model_name_value = getattr(model, 'name', '')
            
            logger.debug(f"check_model_readiness : Checking model: '{model_name_value}' (type: {type(model_name_value)})")
            
            # Check both exact match and prefix match (handles tags like "llama3.1:latest")
            if model_name_value and (model_name_value == model_name or 
                                     model_name_value.startswith(f'{model_name}:') or
                                     model_name_value.startswith(f'{model_name}-')):
                logger.info(f"check_model_readiness : Model '{model_name}' is ready")
                return True
        
        model_names = []
        for model in models:
            if isinstance(model, dict):
                model_names.append(model.get('name', 'N/A'))
            else:
                model_names.append(getattr(model, 'name', 'N/A'))
        
        logger.warning(f"check_model_readiness : Model '{model_name}' not found in available models: {model_names}")
        return False
        
    except Exception as exc:
        logger.error(f"check_model_readiness : Error checking model readiness: {exc}")
        logger.error(f"check_model_readiness : Traceback : {traceback.format_exc()}")
        return False


async def check_ollama_health() -> bool:
    """
    Comprehensive health check for Ollama service.
    
    Performs service availability check only.
    Model pulling is handled separately by pull_model_instance().
    
    Returns:
        bool: True if service is healthy, False otherwise.
    """
    config = get_config()
    
    host = config.get('ollama.host', 'localhost')
    port = config.get('ollama.port', 11434)
    
    max_retries = config.get('ollama.retries.health_check_max', 30)
    retry_interval = config.get('ollama.retries.health_check_interval', 5)
    timeout = config.get('ollama.timeouts.health_check', 10)
    
    logger.info("check_ollama_health : Execution Start")
    logger.info("check_ollama_health : Starting Ollama service health check...")
    
    # Retry loop for service availability
    for attempt in range(1, max_retries + 1):
        logger.debug(f"check_ollama_health : Health check attempt {attempt}/{max_retries}")
        
        if attempt > 1:
            logger.info(f"check_ollama_health : Retrying in {retry_interval}s...")
            await asyncio.sleep(retry_interval)
        
        service_running = await check_service_running(host, port, timeout)
        
        if service_running:
            logger.info(f"check_ollama_health : Service is running on {host}:{port}")
            logger.info("check_ollama_health : Execution End")
            return True
        else:
            logger.warning(f"check_ollama_health : Service not responding on {host}:{port} (attempt {attempt}/{max_retries})")
    
    # All retries exhausted
    error_msg = f"check_ollama_health : Service did not become healthy after {max_retries} attempts"
    logger.error(error_msg)
    logger.info("check_ollama_health : Execution End")
    return False


async def wait_for_ollama(host: Optional[str] = None, port: Optional[int] = None) -> bool:
    """
    Wait for Ollama service to become available.
    
    Convenience function that wraps check_ollama_health with optional
    host/port overrides.
    
    Args:
        host: Optional host override (uses config if not provided).
        port: Optional port override (uses config if not provided).
        
    Returns:
        bool: True if service becomes healthy, False otherwise.
    """
    config = get_config()
    
    if host is None:
        host = config.get('ollama.host', 'localhost')
    if port is None:
        port = config.get('ollama.port', 11434)
    
    return await check_ollama_health()
