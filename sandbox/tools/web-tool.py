from fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("MyDemoServer")

@mcp.tool()
def add(a: int, b: int):
  """Call this tool when you need to add 2 numbers"""
  return a + b


if __name__ == "__main__":
  mcp.run()