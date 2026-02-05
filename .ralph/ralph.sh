#!/bin/bash

# Configuration
MAX_ITERATIONS=${MAX_ITERATIONS:-2}
TOOL_SCRIPT="/opt/ralph/agent.py"

echo "Starting Ralph Loop"
echo "Model: ${OLLAMA_MODEL:-default}"
echo "Max Iterations: $MAX_ITERATIONS"

# Define the stop function
function check_completion() {
    if grep -q "<promise>COMPLETE</promise>" <<< "$1"; then
        echo "✅ Ralph completed all tasks!"
        exit 0
    fi
}

for ((i=1; i<=MAX_ITERATIONS; i++)); do
    echo ""
    echo "==============================================================="
    echo "  Ralph Iteration $i of $MAX_ITERATIONS"
    echo "==============================================================="
    
    # Run the agent script and capture output
    # We use 'tee' to show output live and capture it
    OUTPUT=$(python3 "$TOOL_SCRIPT" 2>&1 | tee /dev/tty)
    
    # Check for completion
    check_completion "$OUTPUT"
    
    echo "Iteration $i complete. Waiting 2 seconds..."
    sleep 2
done

echo "❌ Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
exit 1
