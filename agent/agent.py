import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastmcp.client import Client as MCPClient
from fastmcp.client.transports import StreamableHttpTransport

load_dotenv()

MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

openai = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ.get('OPENAI_API_KEY')
)
mcp_client = MCPClient(StreamableHttpTransport(url="http://127.0.0.1:8000/mcp"))


async def stream(messages):
  response = openai.chat.completions.create( model=MODEL, messages= messages, stream=True )
  for event in response:
      print(event.choices[0].delta.content, end="", flush=True)


async def main():
  # await stream(messages = [{"role": "user", "content": "Hi!"}])
  async with mcp_client:
    await mcp_client.ping()
    tools = await mcp_client.list_tools()
    print(tools)
  
if __name__ == "__main__":
  asyncio.run(main())


