import asyncio
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STATE_FILE = Path(__file__).resolve().with_name("mcp_server_port.txt")
SERVER_SCRIPT = Path(__file__).resolve().with_name("product_search_server.py")


def is_mcp_server_reachable(url: str) -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                url,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
                content=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-03-26",
                            "capabilities": {},
                            "clientInfo": {"name": "client", "version": "1.0"},
                        },
                    }
                ),
            )
            return response.status_code == 200
    except Exception:
        return False


def get_server_url() -> str:
    if STATE_FILE.exists():
        port = STATE_FILE.read_text(encoding="utf-8").strip()
        if port:
            url = f"http://127.0.0.1:{port}/mcp"
            if is_mcp_server_reachable(url):
                return url

    for port in range(8000, 9000):
        url = f"http://127.0.0.1:{port}/mcp"
        if is_mcp_server_reachable(url):
            return url
    return "http://127.0.0.1:8000/mcp"


def ensure_server_running(timeout: int = 25) -> str:
    if STATE_FILE.exists():
        port = STATE_FILE.read_text(encoding="utf-8").strip()
        if port:
            url = f"http://127.0.0.1:{port}/mcp"
            if is_mcp_server_reachable(url):
                return url

    subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT)],
        cwd=str(SERVER_SCRIPT.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )

    deadline = time.time() + timeout
    while time.time() < deadline:
        if STATE_FILE.exists():
            port = STATE_FILE.read_text(encoding="utf-8").strip()
            if port:
                url = f"http://127.0.0.1:{port}/mcp"
                if is_mcp_server_reachable(url):
                    return url
        time.sleep(0.5)

    raise RuntimeError("MCP server did not start in time.")


async def main():
    server_url = ensure_server_running()
    print(f"Connecting to MCP server at {server_url}")

    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "client", "version": "1.0"},
        },
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(server_url, headers=headers, content=json.dumps(payload))
        print("Status:", response.status_code)
        print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
