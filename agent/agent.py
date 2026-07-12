import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ.get('OPENAI_API_KEY')
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

async def stream(messages):
  response = openai.chat.completions.create( model=MODEL, messages= messages, stream=True )
  for event in response:
      print(event.choices[0].delta.content, end="", flush=True)
        

async def main():
  await stream(messages = [{"role": "user", "content": "Hi!"}])
  
if __name__ == "__main__":
  asyncio.run(main())


