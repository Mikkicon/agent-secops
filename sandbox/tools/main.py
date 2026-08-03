import tools.fs 
import tools.web
import tools.weather
from tools._mcp import mcp

if __name__ == "__main__":
  mcp.run(transport="http", host="0.0.0.0", port=8000)
