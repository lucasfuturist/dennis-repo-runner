import os
import sys
import json
import time
import argparse
from typing import Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: 'python-dotenv' is not installed.", flush=True)
    print("Please run: pip install python-dotenv", flush=True)
    sys.exit(1)

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: 'google-genai' is not installed.", flush=True)
    print("Please run: pip install google-genai", flush=True)
    sys.exit(1)


SYSTEM_PROMPT = """You are an Expert Systems Architect. Your task is to perform "Context Compression" on a single source code file. 
You will extract the structural and architectural essence of the file while completely discarding implementation details.

Your output must strictly follow this exact Markdown schema. Do NOT wrap your response in markdown code blocks (```). Output the raw text directly.

### `[File Path]`
**Role:** [1 strict sentence explaining the primary architectural responsibility of this file.]
**Key Interfaces:**
- `ClassName` - [1 sentence explaining the entity/model]
- `functionName(params): ReturnType` - [1 sentence explaining the inputs/outputs. Skip private/helper functions.]
- `VariableName / TypeName` - [List critical exported state, constants, or data structures]
**Dependencies:** [Comma-separated list of critical internal modules and external libraries imported]

COMPRESSION RULES (CRITICAL):
1. NO IMPLEMENTATION: Do not explain HOW a function works. No `if` statements, loops, or algorithmic steps. Only WHAT it takes in and WHAT it returns.
2. PRUNE THE NOISE: Ignore local variables, loop counters, temporary state, and internal-only helper functions (e.g., functions starting with `_`).
3. ARCHITECTURE FIRST: If the file is a Controller, mention the Service it calls. If it's a Repository, mention the Database Model it returns.
4. MISSING DATA: If a file has no exports or dependencies, write "None" for that section. Do not omit the section entirely.
"""

def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path: str, data: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="LLM Context Compressor Orchestrator")
    parser.add_argument("--repo-root", required=True, help="Path to the repository root")
    parser.add_argument("--state-dir", required=True, help="Directory containing state JSON files")
    parser.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini model to use")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between API calls (seconds) to prevent rate limits")
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv(os.path.join(args.repo_root, ".env"))

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set in your .env file.", flush=True)
        sys.exit(1)

    # Initialize the new SDK client
    client = genai.Client(api_key=api_key)

    bool_path = os.path.join(args.state_dir, "file_changed_bool.json")
    master_path = os.path.join(args.state_dir, "master_compressed_context.json")

    changed_bool = _load_json(bool_path)
    master_context = _load_json(master_path)

    pending_files = [k for k, v in changed_bool.items() if v == 1]
    total = len(pending_files)

    if total == 0:
        print("No files pending compression. Exiting.", flush=True)
        sys.exit(0)

    print(f"Found {total} files pending compression.", flush=True)

    for i, stable_id in enumerate(pending_files, 1):
        # The flush=True is CRITICAL here so the GUI reads it instantly
        print(f"[{i}/{total}] Processing: {stable_id}...", flush=True)
        
        # stable_id format is "file:src/path/to/file.py"
        rel_path = stable_id.replace("file:", "", 1)
        abs_path = os.path.join(args.repo_root, rel_path)

        if not os.path.exists(abs_path):
            print(f"  -> Warning: File not found on disk: {abs_path}. Skipping.", flush=True)
            continue

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            print(f"  -> Error reading {abs_path}: {e}", flush=True)
            continue

        user_prompt = f"Please compress the following file:\n\nFile Path: {rel_path}\n\n```\n{code_content}\n```"

        try:
            # Call Gemini using the new SDK syntax
            response = client.models.generate_content(
                model=args.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                )
            )
            
            # Transactional Update
            master_context[stable_id] = response.text.strip()
            changed_bool[stable_id] = 0
            
            # Save immediately to prevent data loss on subsequent crashes
            _save_json(master_path, master_context)
            _save_json(bool_path, changed_bool)
            
            print("  -> Success.", flush=True)
            
            # Respect rate limits
            if i < total:
                time.sleep(args.delay)

        except Exception as e:
            print(f"  -> API Request Failed: {e}", flush=True)
            print("  -> Leaving flag as 1 to retry on next run.", flush=True)
            # Do not exit immediately, attempt the next file or allow user to ctrl+c

    print("Compression sync complete.", flush=True)

if __name__ == "__main__":
    main()