import hashlib
import json
import os
from pathlib import Path
from typing import Any
from openai.types.chat import ChatCompletionMessageToolCallUnion
from pydantic import BaseModel
from mcp.types import Tool

CWD = Path(__file__).resolve().parent

# 1. Developers can configure specific rules to block the agent from accessing critical system files or running forbidden commands like curl or rm.
# 2. Do not let users connect to arbitrary servers. Vet and approve servers before they can be used.
# 3. Hash tool descriptions at approval time; alert on change. 
class MCPRBACConfig(BaseModel):
  allowed_domains: list[str] = ["google.com"] # no spoof.mcp
  allowed_commands: list[str] = ["cat"] # no curl
  allowed_tools: dict[str, str] = {}
  web_tools: set[str] = set(["tavily_tavily_search"])
  
  @staticmethod
  def load_config():
    print("Loading config...")
    allowed_tools: dict[str, str] = {}
    try:
      with open(os.path.join(CWD, "config.json"), "r") as f:
        cfg = json.load(f)
        allowed_tools = cfg.get("allow", {})
        print("Loaded Config:", allowed_tools.keys())
    except Exception as e:
      print("Exception", e)
    return MCPRBACConfig(allowed_tools=allowed_tools)


  def update_allowed_tools(self, tools: list[Tool]):
    allowed_tools = {**self.allowed_tools}
    stale_hash_tools = [t for t in tools if t.name in allowed_tools and hash_tool(t.name, t.description, t.inputSchema) != allowed_tools[t.name]]
    unverified_tools = [t for t in tools if t.name not in allowed_tools]
    # APPROVE + HASH
    for t in stale_hash_tools:
      isapproved = input(f"\n> NAME:{t.name} \n> DESCRIPTION:{t.description}\n> SCHEMA:{json.dumps(t.inputSchema, indent=2)}\n> [TOOL CHANGED SINCE APPROVED] APPROVE {t.name}? Y/N...")
      if isapproved.lower() == "y":
        hash = hash_tool(t.name, t.description, t.inputSchema)
        allowed_tools[t.name] = hash
        print(f"Approved: {t.name} - {hash}")
    for t in unverified_tools:
      isapproved = input(f"\n> NAME:{t.name} \n> DESCRIPTION:{t.description}\n> SCHEMA:{json.dumps(t.inputSchema, indent=2)}\n> APPROVE {t.name}? Y/N...")
      if isapproved.lower() == "y":
        hash = hash_tool(t.name, t.description, t.inputSchema)
        allowed_tools[t.name] = hash
        print(f"Approved: {t.name} - {hash}")
    print("Total new Approved:\n", "\n-".join([f"{k} - {v}" for k,v in allowed_tools.items()]))
    # UPDATE CONFIG
    _config = {"allow": {}}
    try:
      with open(os.path.join(CWD, "config.json"), "r") as f:
        _config = json.load(f)
    except Exception as e:
      print(F"Exception: {e}")
    _config["allow"] = allowed_tools
    with open(os.path.join(CWD, "config.json"), "w") as f:
      print("Writing", _config)
      json.dump(_config, f, indent=2)
    
  
def hash_tool(name, desc, input_schema):
    tohash:str = name + desc + json.dumps(input_schema, sort_keys=True)
    return hashlib.sha256(tohash.encode()).hexdigest()
  


def tool_guard(tool_name: str, config: MCPRBACConfig):
  """ CLAUDE - "permissions": { "allow": [ "WebSearch", "WebFetch(domain:gofastmcp.com)" ] }
  """
  if tool_name in config.allowed_tools.keys():
    return True
  return False


TOOL_CACHE = {}




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
  
  
  
