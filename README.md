# MyRalph

MyRalph is an implementation of the "Ralph Loop" agentic strategy. It runs an autonomous developer agent inside a secure Docker container that iteratively works on your project to complete tasks defined in markdown.

The system connects to your local LLM (via Ollama) and executes a loop of: reading tasks, implementing code, running checks, and updating progress.

## Features

- **Local Execution:** Runs entirely on your machine.
- **Sandboxed:** executed inside a Docker container for security.
- **Model Agnostic:** Connects to any model provided by your local Ollama instance (default: `llama3`).
- **Task Driven:** Follows instructions from a simple `TASKS.md` or `PRD.md` file.

## Prerequisites

1. **Docker**: Ensure Docker Desktop is installed and running.
2. **Ollama**: Ensure [Ollama](https://ollama.com/) is installed and running locally.
   - You should have at least one model pulled (e.g., `ollama pull llama3`).

## Usage

### 1. Define your Tasks

Create or edit `TASKS.md` in the root of your project. This is the "to-do" list for the agent.

```markdown
# Tasks
- [ ] Create a hello world script
- [ ] Add a readme file
```

### 2. Start the Agent

Run the start script located in the `.ralph` directory:

```bash
./.ralph/start.sh
```

You can optionally specify the model and maximum number of iterations:

```bash
# Usage: ./start.sh [model_name] [max_iterations]
./.ralph/start.sh llama3 5
```

### 3. Workflow

- The script will build a Docker image `myralph-agent`.
- It mounts your current directory into the container.
- The agent reads instructions, edits files, and communicates with your local Ollama instance.
- Progress is logged, and completed tasks are marked in your markdown files.

## Project Structure

- **`.ralph/`**: Contains the agent infrastructure (Dockerfile, scripts, system prompts).
- **`TASKS.md`**: Your roadmap for the agent.
- **`PRD.md`**: (Optional) Product Requirement Document for higher-level context.

## References

- Concept based on [Ralph by ghuntley](https://ghuntley.com/ralph).
- Original reference implementation: [snarktank/ralph](https://github.com/snarktank/ralph).
