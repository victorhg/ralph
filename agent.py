import os
import sys
import requests
import json
import re
import subprocess

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))
TASKS_FILE = os.environ.get("TASKS_FILE", "TASKS.md")
PROMPT_FILE = "prompt.md"

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"File {path} not found."

def write_file(path, content):
    # Ensure directory exists
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ Written to {path}")

def execute_git_commit(message):
    try:
        # Check if .git exists, if not init
        if not os.path.exists(".git"):
            subprocess.run(["git", "init"], check=True)
            # Configure user for the agent inside this repo
            subprocess.run(["git", "config", "user.name", "MyRalph Agent"], check=False)
            subprocess.run(["git", "config", "user.email", "agent@myralph.local"], check=False)

        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Check if there are changes to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("No changes to commit.")
            return

        # Commit
        subprocess.run(["git", "commit", "-m", message], check=True)
        print(f"✅ Git commit created: {message}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git commit failed: {e}")

def parse_and_execute_tools(response_text):
    # Look for file blocks: <<FILE path="path/to/file">>content<</FILE>>
    file_pattern = r'<<FILE path="([^"]+)">>(.*?)<</FILE>>'
    matches = re.finditer(file_pattern, response_text, re.DOTALL)
    
    executed = False
    for match in matches:
        path = match.group(1)
        content = match.group(2)
        write_file(path, content)
        executed = True
    
    if executed:
        print("Tools executed.")
        
        # Look for commit message
        commit_msg_match = re.search(r'<<COMMIT_MSG>>(.*?)<</COMMIT_MSG>>', response_text, re.DOTALL)
        commit_msg = commit_msg_match.group(1).strip() if commit_msg_match else "Update by MyRalph Agent"
        
        execute_git_commit(commit_msg)
        
    else:
        print("No tool calls found in output.")

def main():
    print(f"🤖 Connected to Ollama at {OLLAMA_HOST} using model {MODEL}")
    
    # Check if tasks file exists
    if not os.path.exists(TASKS_FILE):
        print(f"❌ Error: Tasks file '{TASKS_FILE}' not found.")
        sys.exit(1)

    tasks_content = read_file(TASKS_FILE)
    
    # Construct System Prompt
    # Load prompt.md to use as system prompt
    system_prompt = read_file(PROMPT_FILE)


    prompt = f"TASKS_FILE:\n{tasks_content}\n\n"
    
    # Try to provide context of the current directory (limited depth/files to avoid token overflow)
    # For MVP, we just rely on the model 'remembering' or we assume it overwrites full files.
    # A better approach is to list files.
    files_list = []
    for root, dirs, files in os.walk("."):
        if ".git" in dirs: 
            dirs.remove(".git")
        for file in files:
            files_list.append(os.path.join(root, file))
    
    prompt += "CURRENT PROJECT STRUCTURE:\n" + "\n".join(files_list) + "\n\n"
    prompt += "Please proceed with the next step."

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        print("⏳ Sending request to Ollama...")
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()
        result = response.json()
        
        content = result.get("message", {}).get("content", "")
        print("\n--- Model Output ---\n")
        print(content)
        print("\n--------------------\n")
        
        parse_and_execute_tools(content)
        
        if "<promise>COMPLETE</promise>" in content:
            print("🏁 Received COMPLETE signal.")
            sys.exit(0) # Logic handled by loop script usually, but we can signal strict exit here?
                        # Since ralph.sh checks the output for the tag, we just need to print it.
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error querying Ollama: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
