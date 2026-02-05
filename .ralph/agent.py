import os
import sys
import requests
import json
import re
import subprocess

AI_PROVIDER = os.environ.get("AI_PROVIDER", "ollama").lower()
MODEL = os.environ.get("AI_MODEL", os.environ.get("OLLAMA_MODEL", "llama3"))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
AI_API_KEY = os.environ.get("AI_API_KEY", "")

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "10"))
TASKS_FILE = os.environ.get("TASKS_FILE", "TASKS.md")
PROMPT_FILE = os.environ.get("PROMPT_FILE", "/opt/ralph/prompt.md")

class LLMProvider:
    def chat(self, system_prompt, messages):
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def chat(self, system_prompt, messages):
        url = f"{OLLAMA_HOST}/api/generate"
        
        full_prompt = f"System: {system_prompt}\n"
        for msg in messages:
            role = msg["role"].capitalize()
            full_prompt += f"{role}: {msg['content']}\n"
        full_prompt += "Assistant: "

        payload = {
            "model": MODEL,
            "prompt": full_prompt,
            "stream": True
        }
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                json_line = json.loads(line.decode('utf-8'))
                chunk = json_line.get("response", "")
                yield chunk

class OpenAIProvider(LLMProvider):
    def chat(self, system_prompt, messages):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {AI_API_KEY}"}
        payload = {
            "model": MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True
        }
        
        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_str = line_text[6:].strip()
                    if data_str == "[DONE]":
                        break
                    json_data = json.loads(data_str)
                    chunk = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if chunk:
                        yield chunk

class ClaudeProvider(LLMProvider):
    def chat(self, system_prompt, messages):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": MODEL,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": 4096,
            "stream": True
        }
        
        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_str = line_text[6:].strip()
                    json_data = json.loads(data_str)
                    if json_data.get("type") == "content_block_delta":
                        yield json_data.get("delta", {}).get("text", "")

def get_provider():
    if AI_PROVIDER == "openai":
        return OpenAIProvider()
    elif AI_PROVIDER == "claude":
        return ClaudeProvider()
    return OllamaProvider()

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
    print(f"   Provider: {AI_PROVIDER}")
    print(f"   Model: {MODEL}")

    # 1. Load System Prompt
    system_prompt = read_file(PROMPT_FILE)
    if "Error" in system_prompt:
        system_prompt = "You are a helpful coding agent."

    # 2. Load Tasks
    tasks_content = read_file(TASKS_FILE)
    
    # 3. Load Context
    context_files = ""
    if os.path.exists("progress.txt"):
        context_files += f"\n=== progress.txt ===\n{read_file('progress.txt')}\n"
    if os.path.exists("AGENTS.md"):
        context_files += f"\n=== AGENTS.md ===\n{read_file('AGENTS.md')}\n"

    # 4. List Files
    files_list = get_project_files(".")
    file_structure = "\n".join(files_list)

    # 5. Build prompt from scratch (Stateless turn)
    prompt = f"""
PROJECT CONTEXT:
Here is the file structure:
{file_structure}

TASKS:
{tasks_content}

CURRENT PROGRESS, FINDINGS & LOGS:
{context_files}

---
Based on the above, proceed with the next step. If you just performed an action, verify it. 
If the task is complete, end your response with <promise>COMPLETE</promise>.
"""

    messages = [{"role": "user", "content": prompt}]
    provider = get_provider()
    
    try:
        assistant_content = ""
        print("\n--- Model Output ---\n")
        
        for chunk in provider.chat(system_prompt, messages):
            assistant_content += chunk
            print(chunk, end='', flush=True)
        
        print("\n\n--------------------\n")
        
        # Execute Tools for this turn
        parse_and_execute_tools(assistant_content)
        
        # Completion check is handled by the bash script via stdout
        if "<promise>COMPLETE</promise>" in assistant_content:
            print("✅ Turn complete: Task Success.")

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
