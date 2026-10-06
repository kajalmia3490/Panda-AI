import os
import json
import time
from typing import List, Dict, Any, Callable
from google import genai
from google.genai import types

from agent.config import GEMINI_API_KEY, DEFAULT_MODEL, AGENT_NAME
from agent.tools import (
    list_files, read_file, write_file, run_command, search_in_files,
    search_windows_apps, install_windows_app
)

SYSTEM_INSTRUCTION = f"""You are {AGENT_NAME} (প্যান্ডা), an elite autonomous Local Coding & PC Assistant AI Agent running directly on the user's computer.

Language, Wake Word & Persona:
- When the user calls you or says "Hey Panda", "হেই প্যান্ডা", "প্যান্ডা", "Panda" or asks if you are there, reply warmly and respectfully:
  "জী বস! বলুন, আমি আপনার জন্য কী করতে পারি? (Ji boss! How can I help you?)"
- You fully understand and speak Bangla (বাংলা) fluently as well as English.
- Always address the user politely ("বস" / "Boss") and provide responses in natural Bangla when addressed in Bangla.
- Introduce yourself as {AGENT_NAME} (প্যান্ডা) when asked.
- Keep technical terms, code snippets, package IDs, and commands precise.

Autonomous Tools & Capabilities:
- `list_files(directory)`: Explore workspace directory structure.
- `read_file(filepath, max_lines)`: Read source code and files.
- `write_file(filepath, content)`: Create new code files or update existing ones.
- `run_command(command)`: Execute terminal/PowerShell commands in workspace.
- `search_in_files(pattern, file_pattern)`: Search codebase for functions or patterns.
- `search_windows_apps(app_name)`: Search for Windows applications available to install via winget (e.g. Chrome, VS Code, Git, VLC, 7zip, Node.js).
- `install_windows_app(package_id_or_name)`: Install a Windows application on the PC silently using winget.

Execution Philosophy:
1. When asked to install apps on the PC, use `search_windows_apps` or `install_windows_app` directly to install them.
2. When asked to code, debug, create, or test, ACT autonomously using your tools.
3. Keep the user informed with clear, structured explanations in their preferred language.
"""

TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search_in_files": search_in_files,
    "search_windows_apps": search_windows_apps,
    "install_windows_app": install_windows_app,
}

TOOL_DECLARATIONS = [
    {
        "name": "list_files",
        "description": "List files and folders in a workspace directory.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "directory": {
                    "type": "STRING",
                    "description": "Relative or absolute directory path (defaults to '.')"
                }
            }
        }
    },
    {
        "name": "read_file",
        "description": "Read the content of a file up to max_lines.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filepath": {
                    "type": "STRING",
                    "description": "Path to the file to read"
                },
                "max_lines": {
                    "type": "INTEGER",
                    "description": "Maximum lines to read (default 500)"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite content into a file. Creates directories if necessary.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filepath": {
                    "type": "STRING",
                    "description": "Path to the file to create or overwrite"
                },
                "content": {
                    "type": "STRING",
                    "description": "Complete text/code content of the file"
                }
            },
            "required": ["filepath", "content"]
        }
    },
    {
        "name": "run_command",
        "description": "Execute a shell / terminal command in the workspace.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Command line string to execute in shell"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "search_in_files",
        "description": "Search for text pattern in files across workspace.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "pattern": {
                    "type": "STRING",
                    "description": "Text pattern to search for"
                },
                "file_pattern": {
                    "type": "STRING",
                    "description": "File glob pattern e.g. *.py"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "search_windows_apps",
        "description": "Search for Windows PC software and applications available to install via winget.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Name or query of the Windows app (e.g. 'chrome', 'git', 'vscode', 'vlc')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "install_windows_app",
        "description": "Install a Windows PC application silently using winget.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "package_id_or_name": {
                    "type": "STRING",
                    "description": "The exact winget Package Id (e.g. 'Git.Git', 'Google.Chrome', 'VideoLAN.VLC', '7zip.7zip') or app name"
                }
            },
            "required": ["package_id_or_name"]
        }
    }
]

class LocalCodingAgent:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or DEFAULT_MODEL
        self.client = genai.Client(api_key=self.api_key)
        self.conversation_history = []  # List of types.Content or dicts

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []

    def set_model(self, model: str):
        self.model = model

    def run_turn(self, user_prompt: str, on_event: Callable[[Dict[str, Any]], None] = None) -> Dict[str, Any]:
        """
        Run an agentic loop turn:
        1. Adds user prompt to conversation.
        2. Queries Gemini with custom tools.
        3. If Gemini outputs function calls:
           - Emits 'tool_call' event
           - Runs local tool
           - Emits 'tool_result' event
           - Sends result back to model
        4. Continues loop until model produces final answer or max iterations reached.
        """
        if on_event:
            on_event({"type": "start", "model": self.model, "prompt": user_prompt})

        # Append user message
        self.conversation_history.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_prompt)]
            )
        )

        max_steps = 15
        step = 0
        final_text = ""

        # Prepare tools configuration
        tools_cfg = [{"function_declarations": TOOL_DECLARATIONS}]

        while step < max_steps:
            step += 1
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=self.conversation_history,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=tools_cfg,
                        temperature=0.3
                    )
                )
            except Exception as e:
                err_msg = f"API Error: {str(e)}"
                if on_event:
                    on_event({"type": "error", "message": err_msg})
                return {"success": False, "error": err_msg, "model": self.model}

            # Check candidate content
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content:
                break

            model_content = candidate.content
            self.conversation_history.append(model_content)

            # Inspect parts
            function_calls = []
            text_parts = []
            for part in (model_content.parts or []):
                if part.function_call:
                    function_calls.append(part.function_call)
                elif part.text:
                    text_parts.append(part.text)

            if text_parts:
                combined_text = "\n".join(text_parts)
                final_text = combined_text
                if on_event:
                    on_event({"type": "thought_or_text", "text": combined_text})

            # If no tool calls, model is finished
            if not function_calls:
                break

            # Execute all requested tool calls
            tool_response_parts = []
            for fc in function_calls:
                fn_name = fc.name
                fn_args = fc.args or {}
                call_id = getattr(fc, 'id', None)

                if on_event:
                    on_event({
                        "type": "tool_call",
                        "tool": fn_name,
                        "args": fn_args
                    })

                # Execute local tool
                tool_fn = TOOL_MAP.get(fn_name)
                if tool_fn:
                    try:
                        result_output = tool_fn(**fn_args)
                    except Exception as ex:
                        result_output = f"Execution error: {str(ex)}"
                else:
                    result_output = f"Error: Tool '{fn_name}' is not recognized."

                if on_event:
                    on_event({
                        "type": "tool_result",
                        "tool": fn_name,
                        "result": result_output
                    })

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result_output}
                    )
                )

            # Append tool execution results back to history for Gemini
            self.conversation_history.append(
                types.Content(
                    role="user",
                    parts=tool_response_parts
                )
            )

        if on_event:
            on_event({"type": "done", "final_text": final_text})

        return {
            "success": True,
            "final_text": final_text,
            "steps": step,
            "model": self.model
        }
