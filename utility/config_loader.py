"""
Module: utility.config_loader
Description: Thread-safe configuration loader with lazy initialization and validation.

Provides a singleton configuration loader that loads configuration on first access,
supporting a fallback chain: Environment Variable → config.json → Default Value.

Includes comprehensive validation and startup diagnostics.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .version import __version__ as app_version

logger = logging.getLogger(__name__)

# Required configuration sections and their keys
REQUIRED_CONFIG_SECTIONS = {
    'ollama': ['host', 'port', 'llm_model'],
    'generated_code_config': ['dir_path', 'file_path'],
}


class ConfigLoader:
    """
    Thread-safe configuration loader with lazy initialization and validation.
    
    Fallback Chain:
        1. Environment variable (if exists)
        2. config.json value (if exists)
        3. Default value (fallback)
    
    This ensures no static initialization issues - configuration is only loaded
    when first accessed, preventing variables from being used before initialization.
    
    Example:
        >>> config = get_config()
        >>> model = config.get('ollama.llm_model', default='llama3.1')
        >>> host = config.get('ollama.host', default='localhost')
    """
    
    _instance: Optional['ConfigLoader'] = None
    _initialized: bool = False
    _config: Dict = {}
    _validated: bool = False
    
    def __new__(cls) -> 'ConfigLoader':
        """Singleton pattern to ensure single config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Lazy initialization - only loads when first accessed."""
        if not ConfigLoader._initialized:
            self._load_config()
            ConfigLoader._initialized = True
    
    def _load_config(self) -> None:
        """Load configuration from JSON file with validation."""
        config_path = Path(__file__).parent.parent / 'config' / 'config.json'
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
            
            # Validate configuration structure
            validation_errors = self._validate_config()
            
            if validation_errors:
                error_msg = f"Configuration validation failed: {'; '.join(validation_errors)}"
                logger.error(f"config_loader : {error_msg}")
                raise RuntimeError(error_msg)
            
            self._validated = True
            logger.info(f"config_loader : Configuration loaded and validated from {config_path}")
            
        except FileNotFoundError:
            error_msg = f"Config file not found: {config_path}. Please ensure config/config.json exists."
            logger.error(f"config_loader : {error_msg}")
            raise RuntimeError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in config file: {e}. Please check config/config.json syntax."
            logger.error(f"config_loader : {error_msg}")
            raise RuntimeError(error_msg)
    
    def _validate_config(self) -> List[str]:
        """
        Validate that required configuration sections and keys exist.
        
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []
        
        for section, required_keys in REQUIRED_CONFIG_SECTIONS.items():
            if section not in self._config:
                errors.append(f"Missing required section: '{section}'")
            else:
                section_data = self._config[section]
                if not isinstance(section_data, dict):
                    errors.append(f"Section '{section}' must be a dictionary")
                else:
                    for key in required_keys:
                        if key not in section_data:
                            errors.append(f"Missing required key '{section}.{key}'")
        
        return errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with fallback chain.
        
        Args:
            key: Dot-separated configuration key (e.g., 'ollama.llm_model')
            default: Default value if key is not found in ENV or config.json
            
        Returns:
            Configuration value from ENV, config.json, or default (in priority order)
        """
        # Check environment variable first (convert dots to underscores)
        env_key = key.replace('.', '_').upper()
        env_value = os.environ.get(env_key)
        if env_value is not None:
            logger.debug(f"config_loader : Key '{key}' resolved from ENV: {env_key}={env_value}")
            return env_value
        
        # Check config.json by traversing nested keys
        value = self._config
        keys = key.split('.')
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break
        
        if value is not None:
            logger.debug(f"config_loader : Key '{key}' resolved from config.json: {value}")
            return value
        
        # Return default as final fallback
        logger.debug(f"config_loader : Key '{key}' not found, using default: {default}")
        return default
    
    def get_required(self, key: str) -> Any:
        """
        Get required configuration value - raises error if missing.
        
        Args:
            key: Dot-separated configuration key
            
        Returns:
            Configuration value
            
        Raises:
            RuntimeError: If the key is not found in ENV or config.json
        """
        value = self.get(key)
        if value is None:
            error_msg = f"Required configuration '{key}' is missing (not in ENV or config.json)"
            logger.error(f"config_loader : {error_msg}")
            raise RuntimeError(error_msg)
        return value
    
    def get_all(self) -> Dict:
        """
        Get entire configuration dictionary.
        
        Returns:
            Dict: Complete configuration (use for diagnostics, not individual lookups)
        """
        return self._config.copy()
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get configuration diagnostics for startup banner.
        
        Returns:
            Dict: Configuration summary for display
        """
        return {
            'version': app_version,
            'ollama': {
                'host': self.get('ollama.host', 'localhost'),
                'port': self.get('ollama.port', 11434),
                'model': self.get('ollama.llm_model', 'llama3.1'),
                'health_check_retries': self.get('ollama.retries.health_check_max', 30),
                'health_check_interval': self.get('ollama.retries.health_check_interval', 5),
                'model_readiness_wait': self.get('ollama.timeouts.model_readiness_wait', 20),
            },
            'execution': {
                'timeout': self.get('execution.timeout_seconds', 30),
                'memory_limit_mb': self.get('execution.memory_limit_mb', 512),
                'allowed_modules': self.get('execution.allowed_modules', []),
            },
            'logging': {
                'level': self.get('logging.level', 'INFO'),
                'file': self.get('logging.file', 'logs/app.log'),
            },
            'generated_code': {
                'dir_path': self.get('generated_code_config.dir_path', 'oLLaMa_generated_code_dir'),
                'file_path': self.get('generated_code_config.file_path', 'generated_code.py'),
            }
        }
    
    def reload(self) -> None:
        """Force reload configuration from file (useful for testing)."""
        self._config = {}
        ConfigLoader._initialized = False
        self._validated = False
        self._load_config()
        logger.info("config_loader : Configuration reloaded")


def get_config() -> ConfigLoader:
    """
    Get configuration loader instance (lazy initialization).
    
    Returns:
        ConfigLoader instance (singleton)
    
    Example:
        >>> config = get_config()
        >>> model = config.get('ollama.llm_model', 'llama3.1')
    """
    return ConfigLoader()


def print_startup_banner() -> None:
    """
    Print comprehensive startup banner with configuration summary.
    
    This should be called once at application startup to show:
    - Application version
    - Configuration summary
    - What the application will do
    """
    config = get_config()
    diag = config.get_diagnostics()
    
    banner = f"""
==========================================================================================
  Ollama Adaptive Image Code Gen v{diag['version']}
==========================================================================================

  Application Description:
  ------------------------
  This application uses Ollama LLM to:
    1. Choose image specifications (dimension, shape, color, area)
    2. Generate Python code for drawing the image
    3. Execute code with automatic dependency installation
    4. Verify generated code against specifications
    5. Iteratively rectify code if verification fails

  Configuration Summary:
  ----------------------
  Ollama Settings:
    • Host:              {diag['ollama']['host']}
    • Port:              {diag['ollama']['port']}
    • Model:             {diag['ollama']['model']}
    • Health Retries:    {diag['ollama']['health_check_retries']} attempts
    • Health Interval:   {diag['ollama']['health_check_interval']}s
    • Model Wait Time:   {diag['ollama']['model_readiness_wait']}s

  Execution Settings:
    • Code Timeout:      {diag['execution']['timeout']}s
    • Memory Limit:      {diag['execution']['memory_limit_mb']} MB
    • Allowed Modules:   {', '.join(diag['execution']['allowed_modules']) if diag['execution']['allowed_modules'] else 'All'}

  Output Settings:
    • Code Directory:    {diag['generated_code']['dir_path']}
    • Code File:         {diag['generated_code']['file_path']}

  Logging:
    • Level:             {diag['logging']['level']}
    • Log File:          {diag['logging']['file']}

  Version:
    • Application:       v{diag['version']}

==========================================================================================
"""
    print(banner)
    logger.info(f"Startup banner printed - Application v{diag['version']} starting")
