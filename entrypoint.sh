#!/bin/bash
set -e

# Pull models
ollama serve

# Execute the default command
exec "$@"
