import asyncio
import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCallUnion
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import Tool
# from openai import OpenAI
from langfuse.openai import OpenAI
from pydantic import BaseModel

from security import MCPRBACConfig, tool_guard


load_dotenv()

MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


mcp_client = MCPClient(
    {
        "mcpServers": {
            # "local": {"url": "http://tools:8000/mcp"}, TODO
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
  
  def __init__(self, config = None, call_config = AgentCallConfig()):
    print("Initial config: ", config)
    self.sec_config = config or MCPRBACConfig.load_config()
    print("Loaded config: ", self.sec_config)
    self._client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)
    self.call_config = call_config

  
  async def ainvoke(self, _messages) -> ChatCompletion:
    unfinished = True
    messages = [{"role": "system", "content": self.call_config.system_prompt}, *_messages]
    while unfinished:
      response = await self.__create(messages)
      print(response)
      choice = response.choices[0]
      messages.append(choice.message)
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
      await mcp_client.ping()
      tools = await mcp_client.list_tools()
      print("\n-".join([t.name for t in tools]))
      MCPRBACConfig.update_allowed_tools(self.sec_config, tools)
      self.sec_config = MCPRBACConfig.load_config()
    print("init - self.sec_config.allowed_tools", self.sec_config.allowed_tools)
    allowed_tools = [t for t in tools if t.name in self.sec_config.allowed_tools ]
    self.tools = [{"type": "function", "function":  {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in allowed_tools]


  @staticmethod
  async def list_tools(mcp_client: MCPClient):
    await mcp_client.ping()
    tools = await mcp_client.list_tools()
    print("\n-".join([t.name for t in tools]))
    return tools


  async def __create(self, messages) -> ChatCompletion:
    return self._client.chat.completions.create(model=MODEL, messages=messages, n=1, tools=self.tools)


  def __should_break(self, response: ChatCompletion):
    return response.choices[-1].finish_reason in ["stop", "length", "content_filter"]


  async def __maybe_add_tool_call(self, response: ChatCompletion, messages: list[Any]):
    choice = response.choices[0]
    if choice.finish_reason == "tool_calls":
      for tool_call in choice.message.tool_calls or []:
        tool_out = await self.__call_tool(tool_call)
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_out.content[0].text})
    return messages
  
  
  async def __call_tool(self, tool_call: ChatCompletionMessageToolCallUnion):
    if not tool_guard(tool_call, self.sec_config): 
      return f"Tool {tool_call.function.name} is forbidden"
    
    args = json.loads(tool_call.function.arguments)
    tool_out = await mcp_client.call_tool(tool_call.function.name, args)
    print("TOOL CALL - ", tool_out)
    return tool_out


  async def __bash(self, command: str):
    # TODO 
    if command not in self.sec_config.allowed_commands:
      return 


def prompt_path():
  CWD = Path(__file__).resolve().parent
  return os.path.join(CWD, "prompts", "sys-linkedin-inbox-v1.md")


async def get_agent():
  system_prompt = ""
  with open(prompt_path(), "r") as f:
    system_prompt = f.read()
  call_config = AgentCallConfig(system_prompt=system_prompt)
  agent = Agent(call_config=call_config)
  await agent.init()
  return agent



async def run():
    # out = await mcp_client.call_tool("local_read_file", {"path": "/data/messages.csv"})
    agent = await get_agent()
    print("agent.tools", agent.tools)
    # print("TOOL CALL - ", out.content[0].text[:200])
    # response = await agent.ainvoke([{"role": "user", "content": "what is the weather today?"}])
    print("\n\nFINAL RESPONSE\n\n")
    # print(response)

async def main():
  await run()

if __name__ == "__main__":
    asyncio.run(main())

# uv run agent.py