from _mcp import mcp

@mcp.tool()
def read_file(path: str):
  """Call this tool when you need to read file"""
  try:
    with open(path, "r") as f:
      content = f.read()
      return content
  except Exception as e:
    return f"ERROR: {e}"

