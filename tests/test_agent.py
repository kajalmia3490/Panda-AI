import os
import pytest
from agent.tools import list_files, read_file, write_file, run_command, search_in_files, _resolve_path
from agent.config import GEMINI_API_KEY, DEFAULT_MODEL, AGENT_NAME
from agent.core import LocalCodingAgent, TOOL_MAP, SYSTEM_INSTRUCTION
from web.server import app

def test_config_values():
    """Test that configuration variables load properly."""
    assert AGENT_NAME == "Lootha"
    assert DEFAULT_MODEL is not None
    assert isinstance(GEMINI_API_KEY, str)

def test_tools_file_operations(tmp_path):
    """Test file writing, reading, listing, and searching in workspace/temp directory."""
    test_file = "test_sample.txt"
    content = "Hello Lootha! This is a comprehensive test suite for the autonomous agent."
    
    # Write file
    write_res = write_file(test_file, content)
    assert "Successfully wrote" in write_res
    
    # Read file
    read_res = read_file(test_file)
    assert content in read_res
    
    # List files
    list_res = list_files(".")
    assert test_file in list_res
    
    # Search in files
    search_res = search_in_files("comprehensive")
    assert test_file in search_res or "comprehensive" in search_res

    # Cleanup
    resolved = _resolve_path(test_file)
    if os.path.exists(resolved):
        os.remove(resolved)

def test_tools_run_command():
    """Test safe shell command execution."""
    res = run_command("python --version")
    assert "Python" in res or "Exit Code: 0" in res

def test_agent_initialization():
    """Test LocalCodingAgent initialization and state resets."""
    agent = LocalCodingAgent()
    assert agent.model == DEFAULT_MODEL
    assert len(agent.conversation_history) == 0
    
    agent.set_model("gemini-2.5-flash")
    assert agent.model == "gemini-2.5-flash"
    
    agent.reset()
    assert len(agent.conversation_history) == 0

def test_tool_mapping():
    """Verify all tool mappings are correctly registered."""
    expected_tools = [
        "list_files",
        "read_file",
        "write_file",
        "run_command",
        "search_in_files",
        "search_windows_apps",
        "install_windows_app"
    ]
    for tool_name in expected_tools:
        assert tool_name in TOOL_MAP
        assert callable(TOOL_MAP[tool_name])

def test_fastapi_server_endpoints():
    """Test FastAPI endpoints using TestClient."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test Root /
    response = client.get("/")
    assert response.status_code == 200
    assert "Lootha" in response.text
    
    # Test Status API
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["agent_name"] == "Lootha"
    assert "models" in data

    # Test Model change API
    response = client.post("/api/model", json={"model": "gemini-2.5-flash"})
    assert response.status_code == 200
    assert response.json()["model"] == "gemini-2.5-flash"

    # Test Session reset API
    response = client.post("/api/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test Workspace files API
    response = client.get("/api/files")
    assert response.status_code == 200
    assert "output" in response.json()
