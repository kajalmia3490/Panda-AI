import sys
import argparse
import uvicorn
from web.server import app
from agent.config import HOST, PORT

def main():
    parser = argparse.ArgumentParser(description="Local Coding AI Agent")
    parser.add_argument("--cli", action="store_true", help="Launch in interactive CLI mode")
    parser.add_argument("--port", type=int, default=PORT, help=f"Web server port (default {PORT})")
    parser.add_argument("--host", type=str, default=HOST, help=f"Web server host (default {HOST})")
    args = parser.parse_args()

    if args.cli:
        from cli import main as cli_main
        cli_main()
    else:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            lan_ip = s.getsockname()[0]
            s.close()
        except Exception:
            lan_ip = "127.0.0.1"

        print("=" * 60)
        print(f"[PC Access]    http://127.0.0.1:{args.port}")
        print(f"[Phone Access] http://{lan_ip}:{args.port}  (Android / iPhone on same Wi-Fi)")
        print("=" * 60)
        uvicorn.run("web.server:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
