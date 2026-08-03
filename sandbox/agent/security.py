import hashlib
from openai.types.chat import ChatCompletionMessageToolCallUnion


# 1. Developers can configure specific rules to block the agent from accessing critical system files or running forbidden commands like curl or rm.
# 2. Do not let users connect to arbitrary servers. Vet and approve servers before they can be used.
# 3. Hash tool descriptions at approval time; alert on change. 
class MCPRBACConfig:
  allowed_domains = ["google.com"] # no spoof.mcp
  allowed_commands = ["cat"] # no curl
  allowed_tools: dict[str, dict] = {"3645...1a37": {}}
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







# 2. Separate Agent Context With/Without external Tools
# Run two separate agents (or sub-agents) that talk over a narrow, typed interface: 
#   privileged executor - dangerous tools (rm, DB, filesystem) and never sees raw external content, and an 
#   untrusted gatherer - external MCP/web tools but has no privileged access. 
# The gatherer's output is treated as data, not instructions — the executor receives it wrapped/quoted (e.g. in a <data> block) so a 
# prompt-injection buried in a fetched page or code file can't issue commands. 
# Apply least privilege to each: 
#   give every tool the tightest scope it needs, and 
#   require explicit user confirmation before any high-privilege or state-changing action crosses the boundary. 
# This way a compromise of the tool-facing side can't reach rm or your database without passing back through the trusted, human-gated executor.
# - strip ANSI escapes, invisible unicode, oversized payloads from tool results before they hit context (your mcp-sanitize.py angle).
# Credential scoping 
# - short-lived, per-tool tokens; secrets never enter model context. 
# - RBAC on tools ≠ RBAC on the keys they hold.
# - append-only record of every call + args; you can't investigate what you didn't log.
# class Agent:
#   pass


# TODO
# def run():
#   privilaged_executor = Agent(tools=["rm", ...])
#   unsafe_gatherer = Agent(tools=["spoof.mcp", ...])

#   while True:
#     result = unsafe_gatherer.run()
#     if len(set([m["tool"]["name"] if m["role"]=="tool" else None for m in result.messages[-10:]])) == 1:
#       # loop of same tool 10 times in a row - stop
#       unsafe_gatherer.stop()
#     result = unsafe_gatherer.tool_call(tools["name"])
#     TOOLS_LOG.append(ToolInvocation(input="...", result=result))





# 3. Human Approval:
# - Claude Code requires explicit developer approval before it runs any sensitive tools or shell commands. 
# - If a poisoned tool tries to silently execute a dangerous script, a human must approve it first.
# - Before the agent executes destructive or data-exfiltrating actions, prompt the user for approval outside the LLM context.


# TODO
# def run():
#   while True:
#     initial = input("sup")
#     messages = [initial]
#     result = privilaged_executor.run()
#     if "ask_user" in result:
#       answer = input(result["ask_user"])
#       messages.append(messages)
  




# 4. Hooks: Pre-tool - server-side restrictions
# - Implement access controls at the tool execution layer so injected instructions cannot override them.
# - This allows the CLI client to vet the action before handing it over to the underlying Large Language Model (LLM).
# - injection is harmless if exfiltration has no route out. 
# Approval fatigue 
# - #4 decays if users rubber-stamp; 
# - batch low-risk, 
# - make destructive prompts visually distinct, 
# - never auto-approve categories.

# TODO
# def run():
#   sandbox = Sandbox(egress=None)
#   stdout = sandbox.run(tools["dangerous_tool_name"])
#   if "rm" in stdout:
#     mcp_config.mcp_tool_blocklist[mcp_name].add("dangerous_tool_name")
#     return "ask_user"
  
  
  
