# no tools. module in container
import os

import tools.fs as fs 
import tools.web as web
import tools.weather as weather
from tools._mcp import mcp

if __name__ == "__main__":
  mcp.run(transport="http", host=os.environ.get("MCP_HOST", "127.0.0.1"), port=8000)

# uv run sandbox/tools/main.py