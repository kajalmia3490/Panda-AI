import os
import json
import time
import base64
from typing import List, Dict, Any, Callable
from google import genai
from google.genai import types

from agent.config import GEMINI_API_KEY, DEFAULT_MODEL, AGENT_NAME
from agent.tools import (
    list_files, read_file, write_file, run_command, search_in_files,
    search_windows_apps, install_windows_app, launch_application,
    close_process, open_url_in_browser, get_system_status,
    control_volume, windows_power_control, move_and_click_mouse,
    keyboard_type_and_press, capture_screenshot, list_open_windows,
    get_clipboard_content, set_clipboard_content,
    live_browser_open, live_browser_interact, live_browser_close
)

SYSTEM_INSTRUCTION = f"""You are {AGENT_NAME} (প্যান্ডা), an autonomous AI PC and Developer Agent with full control over the user's live Windows computer, operating exactly like an expert human software engineer sitting directly in front of the PC with mouse, keyboard, terminal, code editor, and browser.

Real-Life Autonomous PC & Developer Control Mode (Hermes-Style Full Computer Control):
- You have complete control to operate the computer just like a real developer:
  * Inspect screen visually (`capture_screenshot`) to verify UI state, errors, or application windows.
  * Inspect and manage running windows (`list_open_windows`).
  * Open any IDE, application, or tool (`launch_application` e.g. 'code', 'explorer', 'chrome', 'cmd').
  * Read and manipulate clipboard (`get_clipboard_content`, `set_clipboard_content`).
  * Move the mouse across screen and click buttons (`move_and_click_mouse`).
  * Type text, edit code, and execute keyboard hotkeys (`keyboard_type_and_press`).
  * Run any terminal, PowerShell, Git, npm, pip, or Docker command (`run_command`).
  * Create, edit, and inspect full project codebases (`write_file`, `read_file`, `search_in_files`, `list_files`).
  * Install apps and developer toolchains silently via winget (`search_windows_apps`, `install_windows_app`).
- Execute real actions proactively on the computer: Do not just talk or give advice; take real actions on screen and in the system to complete the user's tasks end-to-end.
Language & Communication Rules (ভাষা এবং যোগাযোগ নীতি - বাংলাদেশি বাংলা ও বহুভাষী সাপোর্ট):
- You have fluent native-level support for: **Bangladeshi Bangla (বাংলাদেশি বাংলা - যেমন: "জী বস! আমি এখনই করে দিচ্ছি", "কেমন আছেন?", "কী সাহায্য লাগবে বলুন")**, **Banglish (রোমান হরফে বাংলা, e.g. "kemon acho", "ami ekta kaj korte chai")**, **English**, **Hindi (हिंदी)**, and **Hinglish**.
- **Default & Primary Preference**: Communicate naturally and politely in **Bangladeshi Bangla (বাংলাদেশি বাংলা)** unless the user explicitly uses English or Hindi.
- **Tone & Style in Bangla**: Speak in authentic Bangladeshi tone and accent phrasing (বন্ধুত্বপূর্ণ ও আন্তরিক বাংলাদেশি বাংলা, e.g. "জী বস! একদম চিন্তা করবেন না, আমি এখনই দেখছি", "বস, কাজটা হয়ে গেছে!").
- **Always match the user's language and style**:
  * If the user writes/speaks in **Bangla (বাংলা) or Banglish** -> Always reply in fluent, natural **Bangladeshi Bangla (বাংলাদেশি বাংলা)**!
  * If the user writes/speaks in **English** -> Reply in fluent, clear **English**.
  * If the user writes/speaks in **Hindi (हिंदी) or Hinglish** -> Reply in natural **Hindi / Hinglish**.
- **STRICT NO-EMOJI RULE (ইমোজি সম্পূর্ণ নিষিদ্ধ)**:
  * Do NOT include any emojis (such as 🐼, 💪, 🚀, 😊, etc.) in your replies. Keep your responses completely clean, professional, and text-only without any emojis.
  * Never pronounce, speak, or mention emoji names.
- Always address the user respectfully as "Boss" (বস / बॉस / Boss).
- When the user calls "Hey Panda" / "হেই প্যান্ডা" / "প্যান্ডা":
  * In Bangla / Banglish: "জী বস! বলুন, আমি আপনার জন্য কী করতে পারি?"
  * In English: "Yes Boss! How can I assist you right now?"
  * In Hindi: "जी बॉस! बताइए, मैं आपके लिए क्या कर सकता हूँ?"

CRITICAL ACTION RULES:
1. **ACTION FIRST, DIRECTLY LIVE ON SCREEN (বাস্তব স্ক্রিনে সরাসরি কাজ করা)**:
   - When the user asks to open a website, application, or perform an activity (e.g. "open youtube and search lofi music", "browse news"):
     * Prefer `live_browser_open(url)` to launch a live, visible Chromium browser on the desktop (`headless=False`).
     * Then immediately use `live_browser_interact(action="search", text="...")` or `live_browser_interact(action="click", selector="...")` to perform live actions directly.
     * The user will literally watch the browser open on their screen, type the search query, and play/open the requested content in real-time.
2. **NO UNWANTED SCREENSHOTS**:
   - Do NOT take screenshots repeatedly or unprompted. Only use `capture_screenshot` when the user explicitly asks for a screenshot ("screenshot dao", "screen dekhao", etc.) or if you need to visually debug an unknown UI error.
3. When asked to code, debug, create projects, or control apps:
   - Perform all terminal commands, file creations, and application launches directly.
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
    "capture_screenshot": capture_screenshot,
    "list_open_windows": list_open_windows,
    "get_clipboard_content": get_clipboard_content,
    "set_clipboard_content": set_clipboard_content,
    "live_browser_open": live_browser_open,
    "live_browser_interact": live_browser_interact,
    "live_browser_close": live_browser_close,
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
    },
    {
        "name": "capture_screenshot",
        "description": "Capture a screenshot of the user's active Windows desktop screen to inspect open windows, visual UI, errors, or code.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filename": {
                    "type": "STRING",
                    "description": "File path or name to save screenshot (defaults to 'current_screen.png')"
                }
            }
        }
    },
    {
        "name": "list_open_windows",
        "description": "List all currently visible and open application windows on the Windows desktop with their titles and positions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_clipboard_content",
        "description": "Get current text copied to the Windows clipboard.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "set_clipboard_content",
        "description": "Copy text to the Windows clipboard.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text": {
                    "type": "STRING",
                    "description": "Text to place on the clipboard"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "live_browser_open",
        "description": "Open an interactive Chromium web browser window visibly (headless=False) on screen and navigate to any URL (e.g. 'https://youtube.com', 'https://google.com').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {
                    "type": "STRING",
                    "description": "URL of the website to open live on screen"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "live_browser_interact",
        "description": "Perform live interactive browsing actions in the visible browser on screen: 'search' (searches automatically on YouTube/Google), 'click' (clicks on css selector), 'type' (fills text input), 'scroll_down', 'press' (presses Enter), or 'content' (reads page text).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "'search', 'click', 'type', 'press', 'scroll_down', 'scroll_up', or 'content'"
                },
                "selector": {
                    "type": "STRING",
                    "description": "CSS selector for click/type (optional)"
                },
                "text": {
                    "type": "STRING",
                    "description": "Search keyword or text to type"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "live_browser_close",
        "description": "Close the active visible Playwright browser window.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
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

    def run_turn(
        self,
        user_prompt: str,
        attachments: List[Dict[str, Any]] = None,
        on_event: Callable[[Dict[str, Any]], None] = None
    ) -> Dict[str, Any]:
        """
        Run an agentic loop turn:
        1. Adds user prompt & optional attachments to conversation.
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

        parts = []
        if user_prompt:
            parts.append(types.Part.from_text(text=user_prompt))

        # Process attachments (images, PDFs, text files, code snippets)
        if attachments:
            for att in attachments:
                name = att.get("name", "attachment")
                mime_type = att.get("mime_type") or att.get("type", "application/octet-stream")
                data_b64 = att.get("data")
                if data_b64:
                    try:
                        # Strip header like data:image/png;base64,... if present
                        if "," in data_b64:
                            data_b64 = data_b64.split(",", 1)[1]
                        raw_bytes = base64.b64decode(data_b64)
                        parts.append(
                            types.Part.from_bytes(
                                data=raw_bytes,
                                mime_type=mime_type
                            )
                        )
                    except Exception as e:
                        # Fallback as text reference
                        parts.append(types.Part.from_text(text=f"[Attached file {name} failed to decode: {e}]"))

        if not parts:
            parts.append(types.Part.from_text(text="(Empty message)"))

        # Append user message with all parts (prompt + attachments)
        self.conversation_history.append(
            types.Content(
                role="user",
                parts=parts
            )
        )

        max_steps = 15
        step = 0
        final_text = ""

        # Prepare tools configuration
        tools_cfg = [{"function_declarations": TOOL_DECLARATIONS}]

        fallback_models = [self.model, "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-flash-latest"]
        # Remove duplicates while keeping order
        fallback_models = list(dict.fromkeys(fallback_models))

        while step < max_steps:
            step += 1
            response = None
            last_err = None

            # Retry loop across fallback models if 503 or 429 occurs
            for try_model in fallback_models:
                retries = 2
                for attempt in range(retries):
                    try:
                        response = self.client.models.generate_content(
                            model=try_model,
                            contents=self.conversation_history,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
                                tools=tools_cfg,
                                temperature=0.3
                            )
                        )
                        self.model = try_model  # update active working model
                        last_err = None
                        break
                    except Exception as e:
                        err_str = str(e)
                        last_err = err_str
                        if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                            time.sleep(1.2 * (attempt + 1))
                            continue
                        else:
                            break
                if response:
                    break

            if not response:
                err_msg = f"API Error: {last_err or 'Service temporarily unavailable'}"
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
