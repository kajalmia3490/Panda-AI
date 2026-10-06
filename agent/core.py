import os
import json
import time
from typing import List, Dict, Any, Callable
from google import genai
from google.genai import types

from agent.config import GEMINI_API_KEY, DEFAULT_MODEL, AGENT_NAME
from agent.tools import (
    list_files, read_file, write_file, run_command, search_in_files,
    search_windows_apps, install_windows_app, launch_application,
    close_process, open_url_in_browser, get_system_status,
    control_volume, windows_power_control, move_and_click_mouse,
    keyboard_type_and_press
)

SYSTEM_INSTRUCTION = f"""You are {AGENT_NAME} (প্যান্ডা), an autonomous AI Agent with FULL CONTROL over the user's entire Windows computer system, including live mouse and keyboard automation.

Language, Tone & Persona (বাংলাদেশি ভাষা ও ঢং):
- Speak primarily in natural Bangladeshi Bengali (খাঁটি বাংলাদেশি বাংলা ভাষায় কথা বলুন). Use conversational, respectful, yet friendly tone (যেমন: "জী বস", "হাঁ বস", "একদম ঠিক আছে", "আমি এক্ষুণি করে দিচ্ছি", "কোনো চিন্তা করবেন না").
- Always address the user respectfully as "বস" (Boss).
- When the user calls you or says "Hey Panda", "হেই প্যান্ডা", "প্যান্ডা", "Panda", reply naturally:
  "জী বস! বলুন, কী হুকুম? আমি আপনার জন্য কী করতে পারি?"
- The user has granted you FULL WINDOWS PC ACCESS. Execute all user commands directly and visibly on screen.

Complete Windows System Control Tools:
1. `launch_application(app_or_path)`: Open any app or folder (Explorer, Notepad, Calculator, Chrome, VS Code, etc.).
2. `move_and_click_mouse(x, y, clicks, button)`: Visibly move the mouse across screen and click.
3. `keyboard_type_and_press(text, hotkey)`: Type text or press keys ('win+e' for explorer, 'win', 'enter', 'ctrl+c', etc.).
4. `close_process(process_name)`: Terminate any running program.
5. `open_url_in_browser(url)`: Open websites in the browser.
6. `get_system_status()`: Live CPU, RAM, Battery, and Disk metrics.
7. `control_volume(action)`: Adjust volume ('mute', 'up', 'down').
8. `windows_power_control(action)`: PC power actions ('lock', 'sleep', 'restart', 'shutdown').
9. `search_windows_apps` & `install_windows_app`: Install PC apps via winget.
10. `run_command`: Terminal / PowerShell command runner.
"""

TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search_in_files": search_in_files,
    "search_windows_apps": search_windows_apps,
    "install_windows_app": install_windows_app,
    "launch_application": launch_application,
    "close_process": close_process,
    "open_url_in_browser": open_url_in_browser,
    "get_system_status": get_system_status,
    "control_volume": control_volume,
    "windows_power_control": windows_power_control,
    "move_and_click_mouse": move_and_click_mouse,
    "keyboard_type_and_press": keyboard_type_and_press,
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
    },
    {
        "name": "launch_application",
        "description": "Launch or open any Windows application, file, or executable on the PC (e.g. 'calc', 'notepad', 'chrome', 'explorer', 'code').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_or_path": {
                    "type": "STRING",
                    "description": "Application name or path (e.g. 'calc', 'notepad', 'chrome', 'explorer')"
                }
            },
            "required": ["app_or_path"]
        }
    },
    {
        "name": "close_process",
        "description": "Close or terminate a running program/process on Windows (e.g. 'notepad.exe', 'chrome.exe').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "process_name": {
                    "type": "STRING",
                    "description": "Process name to terminate (e.g. 'notepad.exe', 'calc.exe', 'chrome.exe')"
                }
            },
            "required": ["process_name"]
        }
    },
    {
        "name": "open_url_in_browser",
        "description": "Open a website URL in default browser (e.g. 'https://youtube.com', 'https://google.com').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {
                    "type": "STRING",
                    "description": "URL to open (e.g. 'youtube.com', 'google.com')"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_system_status",
        "description": "Get current Windows system metrics: CPU usage, RAM memory, Battery level, and Disk space.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "control_volume",
        "description": "Control Windows system volume: 'mute', 'unmute', 'up', 'down'.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "'mute', 'unmute', 'up', or 'down'"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "windows_power_control",
        "description": "Control PC power state: 'lock', 'sleep', 'restart', or 'shutdown'.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "'lock', 'sleep', 'restart', or 'shutdown'"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "move_and_click_mouse",
        "description": "Simulate live mouse movement and click on screen. Smoothly glides across screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "x": {
                    "type": "INTEGER",
                    "description": "X coordinate on screen (optional)"
                },
                "y": {
                    "type": "INTEGER",
                    "description": "Y coordinate on screen (optional)"
                },
                "clicks": {
                    "type": "INTEGER",
                    "description": "Number of clicks (1 or 2)"
                },
                "button": {
                    "type": "STRING",
                    "description": "'left', 'right', or 'middle'"
                }
            }
        }
    },
    {
        "name": "keyboard_type_and_press",
        "description": "Simulate live keyboard typing or key combination press (e.g. text='Hello', hotkey='win+e', 'enter', 'ctrl+v').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text": {
                    "type": "STRING",
                    "description": "Text to type out on screen"
                },
                "hotkey": {
                    "type": "STRING",
                    "description": "Key or hotkey combination to press (e.g. 'win+e', 'enter', 'alt+tab')"
                }
            }
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
