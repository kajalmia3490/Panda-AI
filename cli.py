import sys
import io

# Ensure UTF-8 output encoding for Windows PowerShell / Terminal for proper Bangla display
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stdin.encoding.lower() != 'utf-8':
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')

from agent.core import LocalCodingAgent
from agent.config import DEFAULT_MODEL, AGENT_NAME

# Voice engine for CLI
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
except Exception:
    tts_engine = None

def speak(text: str):
    if not tts_engine:
        return
    try:
        # Clean text for speech
        clean_text = text.replace('*', '').replace('#', '').replace('`', '').strip()
        if len(clean_text) > 180:
            clean_text = clean_text[:180] + "..."
        tts_engine.say(clean_text)
        tts_engine.runAndWait()
    except Exception:
        pass

def print_event(e):
    etype = e.get("type")
    if etype == "start":
        print(f"\n[{AGENT_NAME} started using model {e.get('model')}]")
    elif etype == "tool_call":
        args = e.get('args', {})
        print(f"\n  [TOOL CALL] {e.get('tool')}({args})")
    elif etype == "tool_result":
        res = str(e.get('result', ''))
        short_res = res[:250] + ("..." if len(res) > 250 else "")
        print(f"  [RESULT] {short_res.strip()}")
    elif etype == "thought_or_text":
        pass
    elif etype == "error":
        print(f"\n  [ERROR] {e.get('message')}")

def main():
    print("=" * 60)
    print(f"  {AGENT_NAME} (প্যান্ডা) - Local Coding & PC Assistant")
    print("  Voice Enabled (Web + CLI) | Bangla & English")
    print(f"  Model: {DEFAULT_MODEL}")
    print("  Type 'exit' or 'quit' to close. Type 'reset' to clear conversation.")
    print("=" * 60 + "\n")

    agent = LocalCodingAgent()

    while True:
        try:
            prompt = input("You > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "quit"]:
                print("Exiting agent CLI. Goodbye!")
                break
            if prompt.lower() == "reset":
                agent.reset()
                print("Conversation context cleared.\n")
                continue

            # Wake word check: "hey panda"
            lower_p = prompt.lower()
            if lower_p in ["hey panda", "panda", "hello panda", "হেই প্যান্ডা", "প্যান্ডা"]:
                wake_msg = "জী বস! বলুন, আমি আপনার জন্য কী করতে পারি?"
                print(f"\nAgent > {wake_msg}\n" + "-" * 60 + "\n")
                speak(wake_msg)
                continue

            res = agent.run_turn(prompt, on_event=print_event)
            reply = res.get("final_text", "").strip()
            print("\nAgent >")
            print(reply)
            print("-" * 60 + "\n")
            speak(reply)
        except KeyboardInterrupt:
            print("\nSession interrupted.")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
