import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.5-flash-lite")
AGENT_NAME = "Panda"
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

AVAILABLE_MODELS = [
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite (High Reliability)", "recommended": True},
    {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite", "recommended": False},
    {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite", "recommended": False},
    {"id": "gemini-flash-latest", "name": "Gemini Flash Latest", "recommended": False},
    {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash", "recommended": False},
]
