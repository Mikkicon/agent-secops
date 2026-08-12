from tools._mcp import mcp

@mcp.tool()
def read_file(path: str, offset:int = 0, lines_count: int = 20):
  """Call this tool when you need to read files - especially large.
  Starting from offset and getting lines_count lines.
  returns f.readlines()[offset: lines_count]
  default offset = 0, lines_count = 20
  to read whole file - offset = 0, lines_count = -1
  """
  try:
    with open(path, "r") as f:
      content = f.readlines()
      return content[offset: lines_count]
  except Exception as e:
    return f"ERROR: {e}"

