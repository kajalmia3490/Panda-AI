# Panda (প্যান্ডা) 🐼 | Autonomous Local Coding & PC Assistant AI

Panda is an autonomous, locally-hosted coding and PC assistant agent powered by Google Gemini API. It runs directly on your machine, supports natural bilingual communication in **Bangla (বাংলা) & English**, takes **voice commands**, and executes system-level tasks like writing code and installing Windows applications.

---

## 🌟 Key Features

- **🗣️ Voice Commands & Wake Word**:
  - Responds immediately to **"Hey Panda"** / **"হেই প্যান্ডা"** with voice and text: *"জী বস! বলুন, আমি আপনার জন্য কী করতে পারি?"*
  - Real-time speech recognition (Speech-to-Text) and natural voice replies (Text-to-Speech).
- **📱 Multi-Device Support (Android & iOS)**:
  - Accessible on your local Wi-Fi from smartphones (Android / iPhone) or tablets.
  - Responsive mobile UI ready for "Add to Home Screen" as a web app.
- **💻 Windows PC App Installation**:
  - Integrated with Windows Package Manager (`winget`).
  - Search and silently install applications (Chrome, VS Code, Git, VLC, 7-Zip, etc.) via voice or prompt.
- **🛠️ Autonomous Coding Capabilities**:
  - Workspace exploration (`list_files`)
  - File reading & code analysis (`read_file`)
  - Code generation & updates (`write_file`)
  - Shell / PowerShell execution (`run_command`)
  - Full-text search across codebase (`search_in_files`)
- **🌐 Modern Dark-Themed Web UI & CLI Mode**:
  - Live streaming tool execution activity timeline.
  - Interactive file explorer with quick action buttons.

---

## 🚀 Quick Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/kajalmia3490/Panda-AI.git
cd Panda-AI
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory (refer to `.env.example`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_MODEL=gemini-3.5-flash-lite
HOST=0.0.0.0
PORT=8000
```

---

## 💻 Running Panda

### Web Dashboard (Recommended)
```bash
python run.py
```
- **PC Access:** `http://127.0.0.1:8000`
- **Phone Access:** `http://<your-pc-lan-ip>:8000` *(displayed in terminal on startup)*

### Interactive Terminal CLI
```bash
python run.py --cli
```

---

## 📄 License
MIT License.
