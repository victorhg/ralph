#!/bin/bash

# Configuration
# MAX_ITERATIONS is now handled inside agent.py, but we can pass it via ENV
export MAX_ITERATIONS=${MAX_ITERATIONS:-10}
export OLLAMA_MODEL=${OLLAMA_MODEL:-codellama:7b}
TOOL_SCRIPT="/opt/ralph/agent.py"

echo "🚀 Starting Ralph Agent"
echo "   Model: $OLLAMA_MODEL"
echo "   Max Iterations: $MAX_ITERATIONS"
echo "==============================================================="

# Run the python agent directly. 
# It handles its own loop and memory.
python3 "$TOOL_SCRIPT"

echo "==============================================================="
echo "✅ Ralph Session Finished"
