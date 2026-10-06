# 🧪 Lootha (লুথা) Autonomous Agent - Test Suite

This directory contains comprehensive unit and integration tests for **Lootha**, your elite autonomous Local Coding & PC Assistant AI Agent.

## Test Coverage (`tests/test_agent.py`)

1. **`test_config_values`**: Verifies configuration variables (`AGENT_NAME`, `DEFAULT_MODEL`, `GEMINI_API_KEY`).
2. **`test_tools_file_operations`**: Tests local workspace tools (`write_file`, `read_file`, `list_files`, `search_in_files`) using `tmp_path`.
3. **`test_tools_run_command`**: Validates safe shell command execution (`run_command`).
4. **`test_agent_initialization`**: Verifies agent instantiation, model updating, and history reset logic (`LocalCodingAgent`).
5. **`test_tool_mapping`**: Asserts that all core agent tools (including Windows `winget` integration) are correctly mapped.
6. **`test_fastapi_server_endpoints`**: Integration tests for FastAPI web server endpoints (`/`, `/api/status`, `/api/model`, `/api/reset`, `/api/files`) using `TestClient`.

## Running the Tests

To run the test suite locally, execute:

```bash
python -m pytest
```
