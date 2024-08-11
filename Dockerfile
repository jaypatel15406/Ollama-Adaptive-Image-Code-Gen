# Use the Ollama base image
FROM ollama/ollama:latest

# Set the working directory in the container
WORKDIR /app

# Copy all files from the current directory into the working directory in the container
COPY . /app

# Set executable permissions for the entrypoint script
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint to the custom script
ENTRYPOINT ["/app/entrypoint.sh"]