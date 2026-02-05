FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install requests

# Set default env vars
ENV OLLAMA_HOST="http://host.docker.internal:11434"
ENV OLLAMA_MODEL="llama3"
ENV PYTHONUNBUFFERED=1

# The entrypoint is the shell script. 
# We assume the directory is mounted to /app so ralph.sh is available.
CMD ["bash", "ralph.sh"]
