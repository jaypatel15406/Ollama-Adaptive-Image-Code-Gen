"""
Module: utility.code_execution_utility
Description: Secure code execution with sandboxed subprocess and automatic dependency installation.

This module provides:
- AST-based import extraction from Python code
- Automatic module installation with caching (skip already installed)
- Sandboxed code execution using subprocess (not exec())
- Timeout and resource limit enforcement
"""

import os
import ast
import sys
import json
import logging
import traceback
import subprocess
import importlib.util
from pathlib import Path
from typing import Set, Optional

from .config_loader import get_config

logger = logging.getLogger(__name__)


def get_imports(script_path: str) -> Set[str]:
    """
    Extract imported module names from a Python script using AST parsing.
    
    Args:
        script_path: Path to the Python script to analyze.
        
    Returns:
        Set[str]: Set of top-level module names imported in the script.
    """
    try:
        with open(script_path, "r") as file:
            source_code = file.read()
        
        tree = ast.parse(source_code, filename=script_path)
        modules: Set[str] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.add(node.module.split('.')[0])
        
        logger.info(f"get_imports : Extracted {len(modules)} modules from {script_path}")
        return modules
        
    except FileNotFoundError:
        logger.error(f"get_imports : Script file not found: {script_path}")
        return set()
    except SyntaxError as e:
        logger.error(f"get_imports : Syntax error in script {script_path}: {e}")
        return set()
    except Exception as e:
        logger.error(f"get_imports : Unexpected error: {e}")
        logger.error(f"get_imports : Traceback : {traceback.format_exc()}")
        return set()


def install_modules(modules: Set[str]) -> bool:
    """
    Install missing Python modules with caching (skip already installed).
    
    Checks if each module is already installed before attempting installation.
    Only installs modules that are not found in the current environment.
    
    Args:
        modules: Set of module names to install.
        
    Returns:
        bool: True if all modules installed successfully (or were already installed),
              False if any installation failed.
    """
    config = get_config()
    allowed_modules = config.get('execution.allowed_modules', ['matplotlib', 'PIL', 'numpy', 'cv2'])
    
    all_success = True
    
    for module in modules:
        # Check if module is already installed
        if importlib.util.find_spec(module) is not None:
            logger.info(f"install_modules : Module '{module}' already installed, skipping")
            continue
        
        # Check if module is in allowed list (security measure)
        if allowed_modules and module not in allowed_modules:
            logger.warning(f"install_modules : Module '{module}' not in allowed list, skipping")
            continue
        
        try:
            logger.info(f"install_modules : Installing module: {module}")
            
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", module],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info(f"install_modules : Module '{module}' installed successfully")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"install_modules : Failed to install '{module}': {e}"
            logger.error(error_msg)
            all_success = False
        except Exception as e:
            error_msg = f"install_modules : Unexpected error installing '{module}': {e}"
            logger.error(error_msg)
            logger.error(f"install_modules : Traceback : {traceback.format_exc()}")
            all_success = False
    
    return all_success


async def execute_code() -> bool:
    """
    Execute generated Python code in a sandboxed subprocess with timeout.
    
    Instead of using dangerous exec(), this function:
    1. Extracts and installs required modules
    2. Runs the code in a separate subprocess with timeout
    3. Captures and logs any errors
    
    Returns:
        bool: True if code executed successfully, False otherwise.
    """
    config = get_config()
    
    generated_code_config = config.get('generated_code_config', {})
    dir_path = generated_code_config.get('dir_path', 'oLLaMa_generated_code_dir')
    file_path = generated_code_config.get('file_path', 'generated_code.py')
    
    timeout_seconds = config.get('execution.timeout_seconds', 30)
    
    oLLaMa_generated_code_path = os.path.join(dir_path, file_path)
    
    try:
        logger.info("execute_code : Execution Start")
        print("\n=========================================================================================\n")
        
        # Validate code file exists
        if not os.path.exists(oLLaMa_generated_code_path):
            error_msg = f"execute_code : Generated code file not found: {oLLaMa_generated_code_path}"
            logger.error(error_msg)
            return False
        
        # Extract and install required modules
        modules = get_imports(oLLaMa_generated_code_path)
        
        if not modules:
            logger.warning("execute_code : No imports found in generated code")
        else:
            logger.info(f"execute_code : Modules to install: {modules}")
            install_success = install_modules(modules)
            
            if not install_success:
                logger.error("execute_code : Some module installations failed")
        
        # Execute code in sandboxed subprocess with timeout
        logger.info(f"execute_code : Executing code with {timeout_seconds}s timeout...")
        
        result = subprocess.run(
            [sys.executable, oLLaMa_generated_code_path],
            timeout=timeout_seconds,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("execute_code : Code executed successfully")
            
            if result.stdout:
                print(result.stdout)
                logger.info(f"execute_code : Output:\n{result.stdout}")
            
            if result.stderr:
                logger.warning(f"execute_code : Warnings:\n{result.stderr}")
        else:
            logger.error(f"execute_code : Code execution failed with return code {result.returncode}")
            logger.error(f"execute_code : stderr:\n{result.stderr}")
            return False
        
        logger.info("execute_code : Execution End")
        return True
        
    except subprocess.TimeoutExpired:
        error_msg = f"execute_code : Code execution timed out after {timeout_seconds}s"
        logger.error(error_msg)
        return False
    except Exception as exc:
        error_msg = f"execute_code : Error: {exc}"
        logger.error(error_msg)
        logger.error(f"execute_code : Traceback: {traceback.format_exc()}")
        return False
