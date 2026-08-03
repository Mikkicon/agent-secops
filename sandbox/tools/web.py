from _mcp import mcp

@mcp.tool()
def add(a: int, b: int):
  """Call this tool when you need to add 2 numbers"""
  return a + b

