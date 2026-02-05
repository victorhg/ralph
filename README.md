# Ralph

Ralph is a simple, file-based autonomous coding agent. It operates on a **stateless architecture**, where a main loop (managed by a Bash script) spawns a fresh Python process for each turn. This design ensures robustness and prevents context drift by enforcing strict reliance on persisted state.

Ralph reads your task list, writes code, executes commands, and updates its progress, all while running securely inside a Docker container.

## Features

- **Stateless & Robust:** Checkpointing happens naturally via the filesystem (`progress.txt`, `TASKS.md`). If the agent crashes, it restarts fresh on the next loop.
- **Sandboxed:** All code execution happens inside a Docker container.
- **Multi-Provider:** Support for local models (Ollama) and cloud providers (OpenAI, Anthropic).
- **File-Centric Memory:** The "brain" is just `TASKS.md` and `PRD.md`. No complex vector databases or hidden states.

## Prerequisites

1.  **Docker**: Required for the sandbox environment.
2.  **AI Provider**:
    -   **Local:** [Ollama](https://ollama.com/) running locally (default).
    -   **Cloud:** API Key for OpenAI, Anthropic, etc.

## Setup

0.  **Installation**
    - Copy the contents of `.ralph/` to you project folder
    - add `.ralph/` to you `.gitignore`
    - Create 3 files on the project folder `PRD.md`, `TASKS.md`, `AGENTS.md`

1.  **Configuration**:
    Ralph looks for a configuration file at `.ralph/agents.env`. Create this file to set your provider and keys.

    ```bash
    # Example .ralph/agents.env
    
    # Choose provider: ollama, openai, anthropic, groq
    AI_PROVIDER=ollama
    
    # Choose model
    AI_MODEL=llama3
    
    # Keys (only needed for cloud providers)
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    ```

    *Note: `.ralph/agents.env` is git-ignored by default to protect your secrets.*

2.  **Tasks**:
    Define your goals in `TASKS.md` in the root of your project. Look at the example files to have a better understanding

    ```markdown
    # TASK NAME [NOT DONE]
    - [ ] Create a hello world script
    - [ ] Add a readme file
    ```

## Usage

### Start the Agent

Run the start script to build the container and launch the agent loop:

```bash
./.ralph/start.sh
```

### CLI Overrides

You can override configuration defaults directly from the command line:

```bash
# Use a specific model
./.ralph/start.sh --model gpt-4o

# Run for a specific number of loops (default is usually unlimited or high check limit)
./.ralph/start.sh --loops 10

# Start fresh (clears specific memory files like progress.txt)
./.ralph/start.sh --scratch
```

## How It Works

1.  **Boot**: `start.sh` builds the Docker image and mounts the current directory.
2.  **Loop**: `.ralph/ralph.sh` runs inside the container.
3.  **Act**: In every iteration, it launches a Python script that:
    -   Reads `agents.env`, `TASKS.md`, `PRD.md`, and `progress.txt`.
    -   Generates a prompt for the configured LLM.
    -   Executes the LLM's response (editing files, running commands).
    -   Updates `progress.txt` and check-marks `TASKS.md`.
4.  **Repeat**: The Python process exits, and the Bash loop starts the next iteration.

## Project Structure

-   **`.ralph/`**: Contains the agent's brain and infrastructure.
    -   `start.sh`: Host entry point.
    -   `ralph.sh`: Internal loop controller.
    -   `agents.env`: Configuration and secrets.
    -   `agent.py`: The python logic ran each turn.
-   **`TASKS.md`**: Your instructions to the agent.
-   **`progress.txt`**: The agent's short-term memory of what it just did.
