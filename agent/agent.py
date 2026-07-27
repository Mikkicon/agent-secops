import asyncio
import json
import os
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCallUnion
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import Tool

load_dotenv()

MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)

mcp_client = MCPClient(
    {
        "mcpServers": {
            "local": {"url": "http://127.0.0.1:8000/mcp"},
            "tavily": {"url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"},
        }
    }
)

class MCPRBACConfig:
  allowed_domains = ["google.com"] # no spoof.mcp
  allowed_commands = ["cat"] # no curl
  allowed_tools = [] 

class Agent:
  tools = []
  config: MCPRBACConfig = None
  
  def __init__(self, tools: list[Tool], config):
    self.config = config
    _tools = [t.name for t in tools if t.name in self.config.allowed_tools]
    # TODO tools description hash approved/to-approve
    print("\n-".join([t.name for t in _tools]))
    self.tools = [{"type": "function", "function":  {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in _tools]
  
  
  async def ainvoke(self, messages) -> ChatCompletion:
    unfinished = True
    while unfinished:
      response = await self.__create(messages)
      print(response)
      choice = response.choices[0]
      messages.append(choice.message)
      if self.__should_break(response): break
      messages = await self.__maybe_add_tool_call()
    return response


  async def astream(self, messages):
    response = openai.chat.completions.create(
        model=MODEL, messages=messages, stream=True, tools=self.tools
    )
    for event in response:
        print(event.choices[0].delta.content, end="", flush=True)


  @staticmethod
  async def list_tools(mcp_client: MCPClient):
    await mcp_client.ping()
    tools = await mcp_client.list_tools()
    print("\n-".join([t.name for t in tools]))
    return tools


  async def __create(self, messages) -> ChatCompletion:
    return openai.chat.completions.create(model=MODEL, messages=messages, n=1, tools=self.tools)


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
    args = json.loads(tool_call.function.arguments)
    # TODO add guard for each mcp server with each allowed tools - look at claude.json allowedTools
    # TODO specific guard for web tool
    tool_out = await mcp_client.call_tool(tool_call.function.name, args)
    print("TOOL CALL - ", tool_out)


  async def __bash(self, command: str):
    # TODO 
    if command not in self.config.allowed_commands:
      return 


async def run(mcp_client: MCPClient):
    # out = await mcp_client.call_tool("local_read_file", {"path": "/data/messages.csv"})
    # print("TOOL CALL - ", out.content[0].text[:200])
    agent = Agent(tools=await Agent.list_tools(mcp_client))
    response = await agent.ainvoke([{"role": "user", "content": "tell me what is in /data/messages.csv"}])
    print("\n\nFINAL RESPONSE\n\n")
    print(response)

async def main():
    async with mcp_client:
        await run(mcp_client)


if __name__ == "__main__":
    asyncio.run(main())

# uv run agent.py