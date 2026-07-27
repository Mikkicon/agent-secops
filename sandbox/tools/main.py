import tools.fs 
import tools.web
from tools._mcp import mcp

if __name__ == "__main__":
  mcp.run(transport="http", host="0.0.0.0", port=8000)


# docker run -p 8000:8000 -v "$(pwd)/unsafe-sandbox-data:/data" -t flagship-sandbox