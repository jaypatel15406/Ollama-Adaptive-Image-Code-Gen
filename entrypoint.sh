#!/bin/bash
set -e

# Function to check if the Ollama server is up
check_server() {
    local retries=30
    local wait=5

    echo "Checking if Ollama server is up..."
    for i in $(seq 1 $retries); do
        if curl -s http://localhost:11434/ | grep -q "Ollama is running"; then
        echo "Ollama server is up."
        return 0
        fi
        echo "Ollama server not ready yet. Retrying in $wait seconds..."
        sleep $wait
    done

    echo "Ollama server did not start in time."
    exit 1
}

# Start the Ollama server in the background
echo "Starting Ollama server..."
ollama serve &

# Check if the Ollama server is up and ready
check_server

# Pull the model if it's not already downloaded
MODEL_PATH="/root/.ollama/models/llama3.1"
if [ ! -f "$MODEL_PATH" ]; then
    echo "Model not found. Downloading model..."
    ollama pull llama3.1
else
    echo "Model already exists."
fi

# Run the model
echo "Starting the llama3.1 model..."
ollama run llama3.1 &

# Wait to ensure the model is fully loaded and running
echo "Waiting for llama3.1 model to be ready..."
sleep 20

echo "Ollama server and llama3.1 model are ready."

# Wait for the server process to complete
wait
