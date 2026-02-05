#!/bin/bash

# Configuration
IMAGE_NAME="myralph-agent"
MODEL=${1:-"llama3"} # Default model passed as first arg
ITERATIONS=${2:-10}  # Default iterations passed as second arg

# Get the absolute path of the script directory (.ralph folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Get the parent directory (Project Root)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Building MyRalph Docker image..."
docker build -t $IMAGE_NAME "$SCRIPT_DIR"

echo "🏃 Starting MyRalph Loop..."
echo "Using Model: $MODEL"
echo "Max Iterations: $ITERATIONS"
echo "Project Root: $PROJECT_ROOT"

# Determine host internal address handling (macOS handles host.docker.internal automatically, Linux needs --add-host)
# We add it anyway for compatibility
DOCKER_ARGS="--add-host=host.docker.internal:host-gateway"

if [ -f "$PROJECT_ROOT/TASKS.md" ]; then
    echo "Using existing TASKS.md"
else
    echo "Creating sample TASKS.md"
    echo "# Tasks" > "$PROJECT_ROOT/TASKS.md"
    echo "- [ ] Create a hello world python script named 'hello.py'" >> "$PROJECT_ROOT/TASKS.md"
fi

docker run -it --rm \
    $DOCKER_ARGS \
    -v "$PROJECT_ROOT":/app \
    -e OLLAMA_HOST="http://host.docker.internal:11434" \
    -e OLLAMA_MODEL="$MODEL" \
    -e MAX_ITERATIONS="$ITERATIONS" \
    -e TASKS_FILE="TASKS.md" \
    $IMAGE_NAME
