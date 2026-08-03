# no tools. module in container
import fs 
import web
import weather
from _mcp import mcp

if __name__ == "__main__":
  mcp.run(transport="http", host="0.0.0.0", port=8000)
