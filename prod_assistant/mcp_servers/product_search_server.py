import os
import socket
import sys
from pathlib import Path

STATE_FILE = Path(__file__).resolve().with_name("mcp_server_port.txt")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from prod_assistant.retriever.retrieval import Retriever
from langchain_community.tools import DuckDuckGoSearchRun


def get_available_port(host: str = "127.0.0.1", preferred_port: int = 8000) -> int:
    requested_port = int(os.getenv("MCP_PORT", preferred_port))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, requested_port))
            return requested_port
        except OSError:
            sock.bind((host, 0))
            return sock.getsockname()[1]


port = get_available_port()
os.environ["MCP_PORT"] = str(port)
STATE_FILE.write_text(str(port), encoding="utf-8")
print(f"Starting MCP server on http://127.0.0.1:{port}")

# Initialize MCP server
mcp = FastMCP("hybrid_search", host="127.0.0.1", port=port)

# Load retriever lazily so the server can still start if the DB is unavailable
retriever_obj = None
retriever = None

# LangChain DuckDuckGo tool
try:
    duckduckgo = DuckDuckGoSearchRun()
except Exception:
    duckduckgo = None


def get_retriever():
    global retriever_obj, retriever
    if retriever is None:
        if retriever_obj is None:
            retriever_obj = Retriever()
        retriever = retriever_obj.load_retriever()
    return retriever

# ---------- Helpers ----------
def format_docs(docs) -> str:
    """Format retriever docs into readable context."""
    if not docs:
        return ""
    formatted_chunks = []
    for d in docs:
        meta = d.metadata or {}
        formatted = (
            f"Title: {meta.get('product_title', 'N/A')}\n"
            f"Price: {meta.get('price', 'N/A')}\n"
            f"Rating: {meta.get('rating', 'N/A')}\n"
            f"Reviews:\n{d.page_content.strip()}"
        )
        formatted_chunks.append(formatted)
    return "\n\n---\n\n".join(formatted_chunks)

# ---------- MCP Tools ----------
@mcp.tool()
async def get_product_info(query: str) -> str:
    """Retrieve product information for a given query from local retriever."""
    try:
        docs = get_retriever().invoke(query)
        context = format_docs(docs)
        if not context.strip():
            return "No local results found."
        return context
    except Exception as e:
        return f"Product retrieval is temporarily unavailable: {str(e)}"

@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web using DuckDuckGo if retriever has no results."""
    if duckduckgo is None:
        return "Web search is unavailable because the ddgs package is not installed."
    try:
        return duckduckgo.run(query)
    except Exception as e:
        return f"Error during web search: {str(e)}"

# ---------- Run Server ----------
if __name__ == "__main__":
    mcp.run(transport="streamable-http")