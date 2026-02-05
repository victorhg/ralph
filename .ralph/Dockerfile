FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install requests

# Copy agent logic to a separate system location
WORKDIR /opt/ralph
COPY . /opt/ralph

# Set workspace for the target project
WORKDIR /app

# Set default env vars
ENV PYTHONUNBUFFERED=1
ENV PROMPT_FILE="/opt/ralph/prompt.md"

# Point to the script in the system location
CMD ["bash", "/opt/ralph/ralph.sh"]
