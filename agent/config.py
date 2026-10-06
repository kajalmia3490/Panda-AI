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
    {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite (Fast & Active)", "recommended": True},
    {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Latest Flagship)", "recommended": False},
    {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash", "recommended": False},
    {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "recommended": False},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Deep Reasoning)", "recommended": False},
]
