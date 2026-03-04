#!/usr/bin/env python3
"""
Module: validate_config
Description: Validate configuration files before Docker build/startup.

This script checks:
1. config.json exists and is valid JSON
2. All required sections and keys are present
3. No syntax errors in configuration
4. Value types are correct (ports, timeouts, etc.)

Usage:
    python3 validate_config.py

Returns:
    Exit code 0 if validation passes, 1 if fails
"""

import sys
import json
from pathlib import Path

# Import version from utility module (for display only)
sys.path.insert(0, str(Path(__file__).parent))
from utility.version import __version__ as app_version

# Required configuration sections and their keys
REQUIRED_CONFIG = {
    'ollama': ['host', 'port', 'llm_model'],
    'generated_code_config': ['dir_path', 'file_path'],
}


def validate_config_file(config_path: Path) -> tuple:
    """
    Validate configuration file.
    
    Args:
        config_path: Path to config.json
        
    Returns:
        Tuple of (success: bool, errors: list, warnings: list)
    """
    errors = []
    warnings = []
    
    # Check file exists
    if not config_path.exists():
        errors.append(f"Configuration file not found: {config_path}")
        return False, errors, warnings
    
    # Check valid JSON
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON syntax: {e}")
        return False, errors, warnings
    
    # Check required sections
    for section, required_keys in REQUIRED_CONFIG.items():
        if section not in config:
            errors.append(f"Missing required section: '{section}'")
        else:
            section_data = config[section]
            if not isinstance(section_data, dict):
                errors.append(f"Section '{section}' must be a dictionary, got {type(section_data)}")
            else:
                for key in required_keys:
                    if key not in section_data:
                        errors.append(f"Missing required key: '{section}.{key}'")
    
    # Validate specific values
    if 'ollama' in config and isinstance(config['ollama'], dict):
        port = config['ollama'].get('port')
        if port and (not isinstance(port, int) or port < 1 or port > 65535):
            errors.append(f"Invalid port number: {port} (must be 1-65535)")
        
        model = config['ollama'].get('llm_model')
        if model and not isinstance(model, str):
            errors.append(f"llm_model must be a string, got {type(model)}")
    
    if 'execution' in config and isinstance(config['execution'], dict):
        timeout = config['execution'].get('timeout_seconds')
        if timeout and (not isinstance(timeout, (int, float)) or timeout <= 0):
            errors.append(f"timeout_seconds must be positive number, got {timeout}")
        
        memory = config['execution'].get('memory_limit_mb')
        if memory and (not isinstance(memory, int) or memory <= 0):
            errors.append(f"memory_limit_mb must be positive integer, got {memory}")
    
    if 'logging' in config and isinstance(config['logging'], dict):
        level = config['logging'].get('level')
        if level and level.upper() not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append(f"Invalid logging level: {level} (must be DEBUG/INFO/WARNING/ERROR/CRITICAL)")
    
    success = len(errors) == 0
    return success, errors, warnings


def print_validation_report(success: bool, errors: list, warnings: list, config_path: Path) -> None:
    """Print validation report."""
    print("\n" + "="*70)
    print(" Configuration Validation Report")
    print("="*70)
    print(f" Config File: {config_path}")
    print(f" App Version: {app_version}")
    print("-"*70)
    
    if warnings:
        print("\n⚠ WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if errors:
        print("\n✗ ERRORS:")
        for error in errors:
            print(f"  • {error}")
    
    print("\n" + "="*70)
    if success:
        print("✓ VALIDATION PASSED - Configuration is valid")
    else:
        print(f"✗ VALIDATION FAILED - {len(errors)} error(s) found")
    print("="*70 + "\n")


def main() -> int:
    """Main validation function."""
    config_path = Path(__file__).parent / 'config' / 'config.json'
    
    print(f"\nValidating configuration: {config_path}")
    
    success, errors, warnings = validate_config_file(config_path)
    print_validation_report(success, errors, warnings, config_path)
    
    if success:
        print("✓ Ready for Docker build and deployment!\n")
        return 0
    else:
        print("✗ Please fix the errors above before proceeding.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
