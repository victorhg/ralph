#!/bin/bash

# Configuration
TOOL_SCRIPT="/opt/ralph/agent.py"
MAX_ITERATIONS=${MAX_ITERATIONS:-10}

echo "🚀 Starting Ralph Agent (Stateless Bash Loop)"
echo "   Max Iterations: $MAX_ITERATIONS"
echo "==============================================================="

# Configure Git if variables are present
if [ -n "$GIT_USER_NAME" ]; then
    git config --global user.name "$GIT_USER_NAME"
    echo "git configured: user.name=$GIT_USER_NAME"
fi
if [ -n "$GIT_USER_EMAIL" ]; then
    git config --global user.email "$GIT_USER_EMAIL"
    echo "git configured: user.email=$GIT_USER_EMAIL"
fi

iteration=1
while [ $iteration -le $MAX_ITERATIONS ]; do
    echo ""
    echo "🔄 Turn $iteration/$MAX_ITERATIONS"
    echo "---------------------------------------------------------------"
    
    # Run the agent turn and capture output to check for completion
    TMP_OUT=$(mktemp)
    python3 "$TOOL_SCRIPT" | tee "$TMP_OUT"
    
    # Check if the output contains the completion signal
    if grep -q "<promise>PROJECT COMPLETE</promise>" "$TMP_OUT"; then
        rm "$TMP_OUT"
        echo ""
        echo "✅ Ralph project finished successfully."
        exit 0
    fi
    
    rm "$TMP_OUT"
    iteration=$((iteration + 1))
done

echo ""
echo "⚠️  Reached maximum iterations ($MAX_ITERATIONS) without completion."
echo "==============================================================="
exit 0
