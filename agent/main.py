import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import langfuse
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCallUnion
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import Tool
# from openai import OpenAI
from langfuse.openai import OpenAI
from langfuse import observe
from pydantic import BaseModel

from agent.security import TOOL_CACHE, MCPRBACConfig, tool_guard


load_dotenv()

MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CWD = Path(__file__).resolve().parent
TOOLS_URL = os.environ.get("TOOLS_URL", "http://localhost:8000/mcp")

mcp_client = MCPClient(
    {
        "mcpServers": {
            "local":  {"url": TOOLS_URL},
            "tavily": {"url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"},
        }
    }
)


class AgentCallConfig(BaseModel):
  system_prompt: str = ""

class Agent:
  tools = []
  _client: OpenAI = None
  sec_config: MCPRBACConfig = None
  call_config: AgentCallConfig = None
  
  def __init__(self, config = None, api_key=OPENAI_API_KEY, call_config = AgentCallConfig()):
    print("Initial config: ", config)
    self.sec_config = config or MCPRBACConfig.load_config()
    print("Loaded config: ", self.sec_config)
    self._client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)
    self.call_config = call_config

  @observe(name="Invoke")
  async def ainvoke(self, _messages: list[dict]=[]) -> ChatCompletion:
    i, max_iter = 0, 6
    messages = [{"role": "system", "content": self.call_config.system_prompt}, *_messages]
    while i < max_iter:
      response = await self.__create(messages)
      print(response)
      choice = response.choices[0]
      messages.append(choice.message.model_dump())
      if self.__should_break(response): break
      messages = await self.__maybe_add_tool_call(response, messages)
    return response


  async def astream(self, messages):
    response = self._client.chat.completions.create(
        model=MODEL, messages=messages, stream=True, tools=self.tools
    )
    for event in response:
        print(event.choices[0].delta.content, end="", flush=True)


  async def init(self):
    async with mcp_client:
      tools = await mcp_client.list_tools()
      print("\n-".join([t.name for t in tools]))
      if os.environ.get("SKIP_TOOLS_APPROVAL", "true").lower() != "true":
        MCPRBACConfig.update_allowed_tools(self.sec_config, tools)
      self.sec_config = MCPRBACConfig.load_config()
    allowed_tools = [t for t in tools if t.name in self.sec_config.allowed_tools ]
    print("init - allowed_tools", [t.name for t in allowed_tools])
    self.tools = [{"type": "function", "function":  {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in allowed_tools]


  @staticmethod
  async def list_tools(mcp_client: MCPClient):
    await mcp_client.ping()
    tools = await mcp_client.list_tools()
    print("\n-".join([t.name for t in tools]))
    return tools


  async def __create(self, messages) -> ChatCompletion:
    max_retries = 3
    # ChatCompletion(id=None, choices=None, created=None, model=None, object=None, moderation=None, service_tier=None, system_fingerprint=None, usage=None, error={'message': 'error code: 524\n', 'code': 504})
    for i in range(max_retries):
      result =  self._client.chat.completions.create(model=MODEL, messages=messages, n=1, tools=self.tools)
      if hasattr(result, "error"):
        continue
      else:
        break
    return result


  def __should_break(self, response: ChatCompletion):
    return response.choices[-1].finish_reason in ["stop", "length", "content_filter"]


  async def __maybe_add_tool_call(self, response: ChatCompletion, messages: list[Any]):
    choice = response.choices[0]
    if choice.finish_reason == "tool_calls":
      for tool_call in choice.message.tool_calls or []:
        tool_out = await self.__call_tool(tool_call.function.name, tool_call.function.arguments)
        print("tool_out", tool_out)
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_out})
    return messages
  
  @observe(name="call_tool", as_type="tool", capture_input=True, capture_output=True)
  async def __call_tool(self, name: str, args: str):
    if not tool_guard(name, self.sec_config): 
      valid = ", ".join(self.sec_config.allowed_tools)
      return f"Tool '{name}' is not available. Valid tools: {valid}"
    args_json = json.loads(args)
    cache_key = (name, args)
    if cache_key in TOOL_CACHE:
      tool_out = TOOL_CACHE[cache_key]
    else:
      try:
        tool_out = await mcp_client.call_tool(name, args_json)
      except Exception as e:
        tool_out = f"ERROR calling tool: {str(e)}"
      TOOL_CACHE[cache_key] = tool_out
    print("TOOL CALL - ", tool_out)
    return tool_out.content[0].text if tool_out.content else ""


  async def __bash(self, command: str):
    # TODO 
    if command not in self.sec_config.allowed_commands:
      return 


async def get_agent(**kwargs) -> Agent:
  system_prompt = ""
  with open(os.path.join(CWD, "prompts", "sys-linkedin-inbox-v1.md"), "r") as f:
    system_prompt = "\n".join(f.readlines()[:10])
  with open(os.path.join(CWD, "..", "data", "resume-2024.txt"), "r") as f:
    resume = f.read()
  call_config = AgentCallConfig(system_prompt=system_prompt+resume)
  agent = Agent(call_config=call_config, **kwargs)
  await agent.init()
  return agent


def parse_args():
    p = argparse.ArgumentParser(prog="agent")
    p.add_argument("prompt", nargs="?", default="what is the weather today?",
                   help="user message to send")
    # p.add_argument("-m", "--model", default=MODEL)
    return p.parse_args()


async def run(args):
    agent = await get_agent()
    async with mcp_client:
      response = await agent.ainvoke([{"role": "user", "content": args.prompt}])

async def main():
  await run(parse_args())

if __name__ == "__main__":
    asyncio.run(main())

# uv run agent/agent.py