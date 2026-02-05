import os
import sys
import requests
import json
import re
import subprocess

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "codellama:7b")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "10"))
TASKS_FILE = os.environ.get("TASKS_FILE", "TASKS.md")
PROMPT_FILE = os.environ.get("PROMPT_FILE", "/opt/ralph/prompt.md")

def read_file(path):
    try:
        # Resolve path relative to current working directory if it's not absolute
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        if not os.path.exists(path):
             return f"Error: File {path} does not exist."

        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

def write_file(path, content):
    try:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ Written to {path}"
    except Exception as e:
        return f"Error writing to {path}: {str(e)}"

def execute_git_commit(message):
    try:
        if not os.path.exists(".git"):
            subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.name", "Ralph Agent"], check=False, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "agent@ralph.local"], check=False, stdout=subprocess.DEVNULL)

        subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            return "Git: No changes to commit."

        subprocess.run(["git", "commit", "-m", message], check=True, stdout=subprocess.DEVNULL)
        return f"✅ Git commit: {message}"
    except subprocess.CalledProcessError as e:
        return f"⚠️ Git commit failed: {e}"

import fnmatch


def get_project_files(root_dir="."):
    """
    Returns a list of files in the project, respecting .gitignore if available.
    Uses 'git ls-files' if it's a git repo, otherwise falls back to a basic Python implementation.
    """
    files_list = []
    
    # Method 1: Try using git (most robust for .gitignore)
    try:
        # Check if git is available and inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], 
            cwd=root_dir, 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        # Run git ls-files, respecting .gitignore (--exclude-standard) 
        # listing cached (tracked) and other (untracked) files
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        paths = result.stdout.strip().split('\n')
        # Filter out empty strings and .ralph directory itself if desired, 
        # but generally seeing the config is okay. 
        files_list = [p for p in paths if p]
        
        if files_list:
            return files_list
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Method 2: Fallback Python walker
    ignore_patterns = [".git", "__pycache__", "*.pyc", "*.pyo", ".DS_Store", ".ralph"]
    
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
        except Exception:
            pass
    
    for root, dirs, files in os.walk(root_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, p.rstrip('/')) for p in ignore_patterns)]
        
        for file in files:
            if not any(fnmatch.fnmatch(file, p) for p in ignore_patterns):
                rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                files_list.append(rel_path)
                
    return files_list



def parse_and_execute_tools(response_text):
    print(response_text)
    tool_outputs = []
    
    # Tool: READ
    # Format: <<READ path="path/to/file">>
    read_pattern = r'<<READ path="([^"]+)">>'
    read_matches = re.finditer(read_pattern, response_text)
    for match in read_matches:
        path = match.group(1)
        print(f"📖 Reading {path}...")
        content = read_file(path)
        tool_outputs.append(f"--- FILE CONTENT: {path} ---\n{content}\n------------------------------")

    # Tool: WRITE
    # Format: <<FILE path="...">>content<</FILE>>
    write_pattern = r'<<FILE path="([^"]+)">>(.*?)<</FILE>>'
    write_matches = re.finditer(write_pattern, response_text, re.DOTALL)
    for match in write_matches:
        path = match.group(1)
        content = match.group(2)
        # Strip leading newline if it exists from the tag
        if content.startswith('\n'):
            content = content[1:]
            
        print(f"✍️  Writing {path}...")
        result = write_file(path, content)
        tool_outputs.append(result)

    # Tool: COMMIT
    commit_pattern = r'<<COMMIT_MSG>>(.*?)<</COMMIT_MSG>>'
    commit_match = re.search(commit_pattern, response_text, re.DOTALL)
    if commit_match:
        msg = commit_match.group(1).strip()
        print(f"💾 Committing: {msg}")
        result = execute_git_commit(msg)
        tool_outputs.append(result)

    return tool_outputs

def main():
    print(f"🤖 Ralph Agent Initializing...")
    print(f"   Host: {OLLAMA_HOST}")
    print(f"   Model: {MODEL}")

    # 1. Load System Prompt
    system_prompt = read_file(PROMPT_FILE)
    if "Error" in system_prompt:
        # Fallback if file not found
        system_prompt = "You are a helpful coding agent."

    # 2. Load Tasks
    tasks_content = read_file(TASKS_FILE)
    
    # 3. Load Context (Progress & AGENTS.md heuristics)
    context_files = ""
    if os.path.exists("progress.txt"):
        context_files += f"\n=== progress.txt ===\n{read_file('progress.txt')}\n"
    
    # Simple heuristic: Read AGENTS.md in root if exists
    if os.path.exists("AGENTS.md"):
        context_files += f"\n=== AGENTS.md ===\n{read_file('AGENTS.md')}\n"

    # 4. List Files (Structure)
    files_list = get_project_files(".")
    file_structure = "\n".join(files_list)

    # 5. Build Initial Prompt
    initial_prompt = f"""
PROJECT CONTEXT:
Here is the file structure:
{file_structure}

TASKS:
{tasks_content}

CURRENT PROGRESS & LEARNINGS:
{context_files}

Start by analyzing the request or reading necessary files.
"""

    context = [] # To store conversation history (tokens)
    current_prompt = initial_prompt
    
    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n🔄 Iteration {iteration}/{MAX_ITERATIONS}")

        payload = {
            "model": MODEL,
            "prompt": current_prompt,
            "system": system_prompt, # pass system prompt separately
            "context": context,      # pass history
            "stream": True,
            "options": {
                "num_ctx": 8192 
            }
        }

        try:
            print("⏳ Sending request to Ollama...")
            # Switch to /api/generate
            response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, stream=True)
            response.raise_for_status()
            
            assistant_content = ""
            print("\n--- Model Output ---\n")
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_line = json.loads(decoded_line)
                        # /api/generate returns 'response', not 'message.content'
                        chunk = json_line.get("response", "")
                        assistant_content += chunk
                        print(chunk, end='', flush=True)
                        
                        if json_line.get("done"):
                            # Update context with the new history returned by Ollama
                            context = json_line.get("context", [])
                            break
                    except json.JSONDecodeError:
                        continue
            
            print("\n\n--------------------\n")
            
            # Check for completion
            if "<promise>COMPLETE</promise>" in assistant_content:
                print("✅ Task marked as complete.")
                break

            # Execute Tools
            tool_results = parse_and_execute_tools(assistant_content)
            
            if tool_results:
                observation = "\n".join(tool_results)
                current_prompt = f"TOOL OUTPUTS:\n{observation}\n\nContinue."
            else:
                # If no tools were called, force a continuance
                current_prompt = "Proceed with the next step."

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break

if __name__ == "__main__":
    main()
