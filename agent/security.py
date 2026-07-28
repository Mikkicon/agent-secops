import hashlib
from openai.types.chat import ChatCompletionMessageToolCallUnion



class MCPRBACConfig:
  allowed_domains = ["google.com"] # no spoof.mcp
  allowed_commands = ["cat"] # no curl
  allowed_tools: dict[str, dict] = {""}
  web_tools: set[str] = set(["tavily_tavily_search"])




def tool_guard(tool_call: ChatCompletionMessageToolCallUnion, config: MCPRBACConfig):
  """ CLAUDE - "permissions": { "allow": [ "WebSearch", "WebFetch(domain:gofastmcp.com)" ] }
  """
  tool_name_hash = hashlib.sha256(tool_call.function.name).hexdigest()
  if tool_name_hash not in config.allowed_tools.keys():
    return False
    


def domain_guard(tool_call: ChatCompletionMessageToolCallUnion, config: MCPRBACConfig):
  """ CLAUDE - "permissions": { "allow": [ "WebSearch", "WebFetch(domain:gofastmcp.com)" ] }
  """
  if tool_call.function.name not in config.web_tools:
    return True
  return tool_guard(tool_call, config)