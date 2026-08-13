from tools._mcp import mcp

@mcp.tool()
def read_file(path: str, start:int = 0, end: int = 20):
  """Call this tool when you need to read files - especially large.
  Starting from start and getting end lines.
  returns f.readlines()[start: end]
  default start = 0, end = 20
  to read whole file - start = 0, end = -1
  """
  try:
    with open(path, "r") as f:
      content = f.readlines()
      return content[start:end]
  except Exception as e:
    return f"ERROR: {e}"

