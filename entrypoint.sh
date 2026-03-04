#!/bin/bash
set -e

# =============================================================================
# Ollama Adaptive Image Code Gen - Entrypoint Script
# =============================================================================
# This script handles:
# 1. Ollama server startup
# 2. Health checking with configurable retries
# 3. Model pulling with existence check
# 4. Model readiness verification
# =============================================================================

# Configuration with environment variable overrides and defaults
# These values match config/config.json for consistency
HEALTH_CHECK_MAX_RETRIES="${OLLAMA_HEALTH_CHECK_MAX_RETRIES:-30}"
HEALTH_CHECK_INTERVAL="${OLLAMA_HEALTH_CHECK_INTERVAL:-5}"
MODEL_READINESS_WAIT="${OLLAMA_MODEL_READINESS_WAIT:-20}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

# Function to check if the Ollama server is up
check_server() {
    local retries=1
    local wait=$HEALTH_CHECK_INTERVAL
    
    echo "Checking if Ollama server is up..."
    echo "Configuration: max_retries=$HEALTH_CHECK_MAX_RETRIES, interval=${wait}s"
    
    while [ $retries -le $HEALTH_CHECK_MAX_RETRIES ]; do
        if curl -s http://localhost:$OLLAMA_PORT/ | grep -q "Ollama is running"; then
            echo "✓ Ollama server is up on port $OLLAMA_PORT"
            return 0
        fi
        
        echo "⏳ Ollama server not ready yet (attempt $retries/$HEALTH_CHECK_MAX_RETRIES). Retrying in $wait seconds..."
        sleep $wait
        retries=$((retries + 1))
    done
    
    echo "✗ Ollama server did not start in time after $HEALTH_CHECK_MAX_RETRIES attempts"
    exit 1
}

# Function to check if model is ready
check_model_readiness() {
    local model=$1
    local wait_time=$MODEL_READINESS_WAIT
    
    echo "Waiting for model '$model' to be ready (${wait_time}s)..."
    sleep $wait_time
    
    # Try to query the model list to verify readiness
    if curl -s http://localhost:$OLLAMA_PORT/api/tags | grep -q "$model"; then
        echo "✓ Model '$model' is ready"
        return 0
    else
        echo "⚠ Model '$model' may not be fully loaded yet, proceeding anyway..."
        return 0
    fi
}

# =============================================================================
# Main Script Execution
# =============================================================================

echo "============================================================================="
echo " Ollama Adaptive Image Code Gen - Starting Up"
echo "============================================================================="
echo "Configuration:"
echo "  - Model: $OLLAMA_MODEL"
echo "  - Port: $OLLAMA_PORT"
echo "  - Health Check Max Retries: $HEALTH_CHECK_MAX_RETRIES"
echo "  - Health Check Interval: ${HEALTH_CHECK_INTERVAL}s"
echo "  - Model Readiness Wait: ${MODEL_READINESS_WAIT}s"
echo "============================================================================="

# Start the Ollama server in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for server to be ready
check_server

# Pull the model if it's not already downloaded
MODEL_PATH="/root/.ollama/models"
echo "Checking for model '$OLLAMA_MODEL' in $MODEL_PATH..."

if [ -d "$MODEL_PATH" ] && find "$MODEL_PATH" -name "*${OLLAMA_MODEL}*" -type f | grep -q .; then
    echo "✓ Model '$OLLAMA_MODEL' already exists, skipping pull"
else
    echo "⏳ Model not found. Downloading model '$OLLAMA_MODEL'..."
    ollama pull $OLLAMA_MODEL
    echo "✓ Model '$OLLAMA_MODEL' downloaded successfully"
fi

# Verify model is ready
check_model_readiness $OLLAMA_MODEL

echo "============================================================================="
echo " Ollama server and model '$OLLAMA_MODEL' are ready"
echo "============================================================================="

# Keep the container running and wait for the server process
# The Python application will be started separately via docker-compose command
wait
