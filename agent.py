import os
import sys
import requests
import json
import re

# Configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))
TASKS_FILE = os.environ.get("TASKS_FILE", "TASKS.md")

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
    system_prompt = """You are an autonomous developer agent.
You are running in a loop.
Your goal is to complete the tasks described in the attached tasks file.
You can read files and write files.

To WRITE a file, use the designated format:
<<FILE path="path/to/filename.ext">>
Line 1 of content
Line 2 of content
<</FILE>>

This will overwrite the file at 'path/to/filename.ext' with the content provided.
You can write multiple files in one response.

Check your progress. If you believe all tasks are complete, output:
<promise>COMPLETE</promise>

If you are not done, analyze the current state, decide on the next step, and output the necessary file changes or code.
"""

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
