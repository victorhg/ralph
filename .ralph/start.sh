#!/bin/bash

# Default Configuration
IMAGE_NAME="myralph-agent"
MODEL_ARG=""
ITERATIONS_ARG=""
SCRATCH=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model) MODEL_ARG="$2"; shift ;;
        --loops) ITERATIONS_ARG="$2"; shift ;;
        --scratch) SCRATCH=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Get the absolute path of the script directory (.ralph folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Get the parent directory (Project Root)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Handle scratch mode
if [ "$SCRATCH" = true ]; then
    echo "🧹 Scratch mode: Resetting progress.txt..."
    rm -f "$PROJECT_ROOT/progress.txt"
    touch "$PROJECT_ROOT/progress.txt"
fi

echo "🚀 Building MyRalph Docker image..."
docker build -t $IMAGE_NAME "$SCRIPT_DIR"

echo "🏃 Starting MyRalph Loop..."
[ -n "$MODEL_ARG" ] && echo "Override Model: $MODEL_ARG"
[ -n "$ITERATIONS_ARG" ] && echo "Override Iterations: $ITERATIONS_ARG"
echo "Project Root: $PROJECT_ROOT"

# Determine host internal address handling (macOS handles host.docker.internal automatically, Linux needs --add-host)
# We add it anyway for compatibility
DOCKER_ARGS="--add-host=host.docker.internal:host-gateway"

# Prepare CLI Overrides
CLI_OVERRIDES=""
if [ -n "$MODEL_ARG" ]; then
    CLI_OVERRIDES="$CLI_OVERRIDES -e AI_MODEL=$MODEL_ARG"
fi
if [ -n "$ITERATIONS_ARG" ]; then
    CLI_OVERRIDES="$CLI_OVERRIDES -e MAX_ITERATIONS=$ITERATIONS_ARG"
fi

# Load agents.env if it exists
ENV_FILE=""
if [ -f "$SCRIPT_DIR/agents.env" ]; then
    echo "📄 Loading configuration from agents.env"
    ENV_FILE="--env-file $SCRIPT_DIR/agents.env"
fi

if [ -f "$PROJECT_ROOT/TASKS.md" ]; then
    echo "Using existing TASKS.md"
else
    echo "Creating sample TASKS.md"
    echo "# Tasks" > "$PROJECT_ROOT/TASKS.md"
    echo "- [ ] Create a hello world python script named 'hello.py'" >> "$PROJECT_ROOT/TASKS.md"
fi

docker run -it --rm \
    $DOCKER_ARGS \
    $ENV_FILE \
    $CLI_OVERRIDES \
    -v "$PROJECT_ROOT":/app \
    $IMAGE_NAME
