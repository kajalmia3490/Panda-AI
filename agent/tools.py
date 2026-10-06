import os
import subprocess
import glob
from typing import List, Dict, Any

DEFAULT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _resolve_path(rel_or_abs_path: str) -> str:
    """Resolve a relative or absolute path safely."""
    if os.path.isabs(rel_or_abs_path):
        return os.path.normpath(rel_or_abs_path)
    return os.path.normpath(os.path.join(DEFAULT_BASE_DIR, rel_or_abs_path))

def list_files(directory: str = ".") -> str:
    """List all files and subdirectories in the specified workspace directory."""
    try:
        target = _resolve_path(directory)
        if not os.path.exists(target):
            return f"Error: Directory '{directory}' does not exist."
        
        entries = []
        for root, dirs, files in os.walk(target):
            # Exclude virtualenvs and .git
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
    """Read contents of a file up to max_lines. Provide filepath relative to workspace or absolute."""
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
    """Write or overwrite content to a file. Creates parent directories automatically."""
    try:
        target = _resolve_path(filepath)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        size_kb = round(os.path.getsize(target) / 1024, 2)
        return f"Successfully wrote {len(content)} characters ({size_kb} KB) to '{filepath}'."
    except Exception as e:
        return f"Error writing file '{filepath}': {str(e)}"

def run_command(command: str) -> str:
    """Execute a shell command (PowerShell / Command Prompt on Windows) in the workspace and return stdout and stderr."""
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

def search_in_files(pattern: str, file_pattern: str = "*.*") -> str:
    """Search for text or patterns in workspace files matching file_pattern."""
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

def search_windows_apps(app_name: str) -> str:
    """Search for Windows applications available to install using winget (Windows Package Manager)."""
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
    """Install a Windows PC application using Windows Package Manager (winget) by package ID or exact name.
    Example packages: Git.Git, Google.Chrome, 7zip.7zip, Notepad++.Notepad++, Python.Python.3.12, Microsoft.VisualStudioCode
    """
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
        
        # Fallback without --id if exit code not 0
        if result.returncode != 0 and "." not in package_id_or_name:
            cmd2 = [
                "winget", "install", package_id_or_name,
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--disable-interactivity"
            ]
            result2 = subprocess.run(
                cmd2,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=180
            )
            return f"Install attempt with name:\n{result2.stdout[:800]}\nExit Code: {result2.returncode}"

        return "\n".join(output)
    except Exception as e:
        return f"Error installing application '{package_id_or_name}': {str(e)}"

AGENT_TOOLS = [
    list_files,
    read_file,
    write_file,
    run_command,
    search_in_files,
    search_windows_apps,
    install_windows_app
]
