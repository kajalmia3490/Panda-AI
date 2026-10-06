import os
import subprocess
import glob
import webbrowser
import time
from typing import List, Dict, Any

DEFAULT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _resolve_path(rel_or_abs_path: str) -> str:
    """Resolve a relative or absolute path safely."""
    if os.path.isabs(rel_or_abs_path):
        return os.path.normpath(rel_or_abs_path)
    return os.path.normpath(os.path.join(DEFAULT_BASE_DIR, rel_or_abs_path))

# --- File Operations ---

def list_files(directory: str = ".") -> str:
    """List all files and subdirectories in the specified workspace directory."""
    try:
        target = _resolve_path(directory)
        if not os.path.exists(target):
            return f"Error: Directory '{directory}' does not exist."
        
        entries = []
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.venv', 'node_modules']]
            rel_root = os.path.relpath(root, target)
            prefix = "" if rel_root == "." else rel_root + "/"
            for d in dirs:
                entries.append(f"[DIR]  {prefix}{d}/")
            for f in files:
                full_path = os.path.join(root, f)
                size_kb = round(os.path.getsize(full_path) / 1024, 2)
                entries.append(f"[FILE] {prefix}{f} ({size_kb} KB)")
        
        if not entries:
            return f"Directory '{directory}' is empty."
        return "\n".join(entries[:200])
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def read_file(filepath: str, max_lines: int = 500) -> str:
    """Read contents of a file up to max_lines."""
    try:
        target = _resolve_path(filepath)
        if not os.path.exists(target):
            return f"Error: File '{filepath}' does not exist."
        if os.path.isdir(target):
            return f"Error: '{filepath}' is a directory, not a file."
        
        with open(target, 'r', encoding='utf-8', errors='replace') as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
            return f"--- Content of {filepath} ({len(lines)} lines) ---\n{content}"
    except Exception as e:
        return f"Error reading file '{filepath}': {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Write or overwrite content to a file."""
    try:
        target = _resolve_path(filepath)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        size_kb = round(os.path.getsize(target) / 1024, 2)
        return f"Successfully wrote {len(content)} characters ({size_kb} KB) to '{filepath}'."
    except Exception as e:
        return f"Error writing file '{filepath}': {str(e)}"

def search_in_files(pattern: str, file_pattern: str = "*.*") -> str:
    """Search for text or patterns in workspace files."""
    try:
        matches = []
        for root, dirs, files in os.walk(DEFAULT_BASE_DIR):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.venv', 'node_modules']]
            for f in files:
                if not any(f.endswith(ext) for ext in ['.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.env']):
                    continue
                file_path = os.path.join(root, f)
                rel_path = os.path.relpath(file_path, DEFAULT_BASE_DIR)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                        for idx, line in enumerate(fp, 1):
                            if pattern.lower() in line.lower():
                                matches.append(f"{rel_path}:{idx}: {line.strip()}")
                                if len(matches) >= 50:
                                    break
                except Exception:
                    continue
            if len(matches) >= 50:
                break
        
        if not matches:
            return f"No matches found for '{pattern}'."
        return "\n".join(matches)
    except Exception as e:
        return f"Error searching: {str(e)}"

# --- System & Command Execution ---

def run_command(command: str) -> str:
    """Execute any shell / PowerShell command on the Windows PC and return stdout and stderr."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=DEFAULT_BASE_DIR,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        output = []
        if result.stdout:
            output.append("STDOUT:\n" + result.stdout.strip())
        if result.stderr:
            output.append("STDERR:\n" + result.stderr.strip())
        output.append(f"Exit Code: {result.returncode}")
        return "\n\n".join(output) if output else "Command executed with no output."
    except subprocess.TimeoutExpired:
        return f"Command '{command}' timed out after 60 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

# --- Windows App Management ---

def search_windows_apps(app_name: str) -> str:
    """Search for Windows applications available to install using winget."""
    try:
        cmd = [
            "winget", "search", app_name,
            "--accept-source-agreements",
            "--disable-interactivity"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=25
        )
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            return "\n".join(lines[:25])
        return f"No applications found matching '{app_name}'."
    except Exception as e:
        return f"Error searching Windows apps: {str(e)}"

def install_windows_app(package_id_or_name: str) -> str:
    """Install a Windows application on the PC using winget."""
    try:
        cmd = [
            "winget", "install",
            "--id", package_id_or_name,
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--disable-interactivity"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )
        output = []
        if result.stdout:
            output.append(result.stdout.strip()[:1000])
        if result.stderr:
            output.append("STDERR: " + result.stderr.strip()[:400])
        output.append(f"Exit Code: {result.returncode}")
        return "\n".join(output)
    except Exception as e:
        return f"Error installing application '{package_id_or_name}': {str(e)}"

# --- Complete Windows System Control Tools ---

def launch_application(app_or_path: str) -> str:
    """Launch any Windows program, exe, file, or shortcut (e.g. 'notepad', 'calc', 'chrome', 'explorer', 'cmd', or exact file path)."""
    try:
        os.startfile(app_or_path)
        return f"Successfully opened '{app_or_path}'."
    except Exception as e:
        # Fallback to subprocess start
        try:
            subprocess.Popen(f'start "" "{app_or_path}"', shell=True)
            return f"Started '{app_or_path}'."
        except Exception as ex:
            return f"Error opening '{app_or_path}': {str(ex)}"

def close_process(process_name: str) -> str:
    """Terminate or kill a running application/process by name (e.g. 'chrome.exe', 'notepad.exe', 'calc.exe')."""
    try:
        if not process_name.endswith(".exe"):
            process_name += ".exe"
        cmd = f"taskkill /F /IM {process_name}"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors="replace")
        return res.stdout.strip() or res.stderr.strip() or f"Process {process_name} closed."
    except Exception as e:
        return f"Error closing process '{process_name}': {str(e)}"

def open_url_in_browser(url: str) -> str:
    """Open any URL or search in the default web browser (e.g. 'https://youtube.com', 'https://google.com')."""
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url} in browser."
    except Exception as e:
        return f"Error opening browser URL: {str(e)}"

def get_system_status() -> str:
    """Get real-time Windows system metrics: CPU usage, RAM memory, Battery level, and Disk space."""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        battery = psutil.sensors_battery()
        
        info = [
            f"💻 CPU Usage: {cpu_percent}%",
            f"🧠 RAM Memory: {memory.percent}% used ({round(memory.used / (1024**3), 2)} GB / {round(memory.total / (1024**3), 2)} GB)",
            f"💾 Disk (C:): {disk.percent}% used ({round(disk.free / (1024**3), 2)} GB free / {round(disk.total / (1024**3), 2)} GB)",
        ]
        if battery:
            status = "Plugged In" if battery.power_plugged else "Discharging"
            info.append(f"🔋 Battery: {battery.percent}% ({status})")
        return "\n".join(info)
    except Exception as e:
        return f"Error retrieving system status: {str(e)}"

def control_volume(action: str) -> str:
    """Control Windows master volume: 'mute', 'unmute', 'up', 'down'."""
    try:
        import pyautogui
        action = action.lower().strip()
        if action in ["mute", "unmute"]:
            pyautogui.press("volumemute")
            return "Volume mute toggled."
        elif action in ["up", "increase"]:
            for _ in range(5):
                pyautogui.press("volumeup")
            return "Volume increased."
        elif action in ["down", "decrease"]:
            for _ in range(5):
                pyautogui.press("volumedown")
            return "Volume decreased."
        return f"Unknown volume action '{action}'. Use 'mute', 'up', or 'down'."
    except Exception as e:
        return f"Error controlling volume: {str(e)}"

def windows_power_control(action: str) -> str:
    """Control Windows power state: 'lock', 'sleep', 'restart', or 'shutdown'."""
    try:
        action = action.lower().strip()
        if action == "lock":
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            return "Windows PC locked."
        elif action == "sleep":
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return "Windows PC entered sleep mode."
        elif action == "restart":
            subprocess.run("shutdown /r /t 5", shell=True)
            return "Restarting Windows PC in 5 seconds."
        elif action == "shutdown":
            subprocess.run("shutdown /s /t 10", shell=True)
            return "Shutting down Windows PC in 10 seconds."
        return f"Unknown power action '{action}'. Use 'lock', 'sleep', 'restart', or 'shutdown'."
    except Exception as e:
        return f"Error executing power action: {str(e)}"

AGENT_TOOLS = [
    list_files,
    read_file,
    write_file,
    run_command,
    search_in_files,
    search_windows_apps,
    install_windows_app,
    launch_application,
    close_process,
    open_url_in_browser,
    get_system_status,
    control_volume,
    windows_power_control,
]
