import os
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from agent.config import GEMINI_API_KEY, DEFAULT_MODEL, AVAILABLE_MODELS, WORKSPACE_DIR, HOST, PORT, AGENT_NAME
from agent.core import LocalCodingAgent
from agent.tools import list_files, read_file, write_file, run_command

app = FastAPI(title=f"{AGENT_NAME} - Local Coding AI Agent", version="1.0.0")

# Serve static files
web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
static_dir = os.path.join(web_dir, "static")
templates_dir = os.path.join(web_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Shared active agent instance
agent_instance = LocalCodingAgent()

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None

class SetModelRequest(BaseModel):
    model: str

class ExecuteCommandRequest(BaseModel):
    command: str

class WriteFileRequest(BaseModel):
    filepath: str
    content: str

class ReadFileRequest(BaseModel):
    filepath: str

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = os.path.join(templates_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(f"<h1>{AGENT_NAME} Local Coding Agent</h1><p>UI loading error</p>")

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "agent_name": AGENT_NAME,
        "model": agent_instance.model,
        "models": AVAILABLE_MODELS,
        "workspace": WORKSPACE_DIR,
        "api_key_configured": bool(GEMINI_API_KEY)
    }

@app.post("/api/model")
async def change_model(req: SetModelRequest):
    agent_instance.set_model(req.model)
    return {"status": "success", "model": agent_instance.model}

@app.post("/api/reset")
async def reset_session():
    agent_instance.reset()
    return {"status": "success", "message": "Agent session reset."}

@app.get("/api/files")
async def get_workspace_files(dir: str = "."):
    output = list_files(dir)
    return {"directory": dir, "output": output}

@app.post("/api/file/read")
async def api_read_file(req: ReadFileRequest):
    content = read_file(req.filepath)
    return {"filepath": req.filepath, "content": content}

@app.post("/api/file/write")
async def api_write_file(req: WriteFileRequest):
    res = write_file(req.filepath, req.content)
    return {"filepath": req.filepath, "result": res}

@app.post("/api/command")
async def api_run_command(req: ExecuteCommandRequest):
    output = run_command(req.command)
    return {"command": req.command, "output": output}

@app.get("/api/screenshot")
async def get_latest_screenshot(file: str = "current_screen.png"):
    file_path = os.path.normpath(os.path.join(WORKSPACE_DIR, os.path.basename(file)))
    if not os.path.exists(file_path):
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            img = pyautogui.screenshot()
            img.save(file_path)
        except Exception:
            pass

    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Screenshot not found.")

@app.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent interaction with streamed
    thinking steps, tool calls, execution outputs, and final response.
    """
    await websocket.accept()
    
    # Send welcome connection packet
    await websocket.send_json({
        "type": "connected",
        "agent_name": AGENT_NAME,
        "model": agent_instance.model,
        "workspace": WORKSPACE_DIR
    })

    loop = asyncio.get_event_loop()

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "chat":
                prompt = data.get("prompt", "")
                attachments = data.get("attachments", [])
                selected_model = data.get("model")
                if selected_model:
                    agent_instance.set_model(selected_model)

                # Threadsafe event dispatcher back to websocket
                def emit_event(event_data):
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json(event_data),
                        loop
                    )

                # Run turn in executor so it does not block the event loop
                res = await loop.run_in_executor(
                    None,
                    lambda: agent_instance.run_turn(prompt, attachments=attachments, on_event=emit_event)
                )

            elif action == "reset":
                agent_instance.reset()
                await websocket.send_json({
                    "type": "info",
                    "message": "Conversation history reset."
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

def start_server():
    import uvicorn
    uvicorn.run("web.server:app", host=HOST, port=PORT, reload=False)

if __name__ == "__main__":
    start_server()
