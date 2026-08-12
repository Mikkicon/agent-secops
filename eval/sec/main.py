import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from agent.agent import get_agent
from eval.scorers import LLMJudge

def golden_path():
  CWD = Path(__file__).resolve().parent
  return os.path.join(CWD, "..", "data", "goldens_aug_nov_2024-5.jsonl")

# load_dotenv("/Users/mp/projects/flagship/pentest/.env", override=False) # load read keys

# TODO Prepare Poisoned Artifacts
# MCP Tool Poisoning  -  move get_weather into eval as artifact for testing and expose mcp for agent to add
# Supply Chain Attack Signals  -  verify description hashing works
# Direct Prompt Injection  -  write prompts with injections
# Multilingual Variants  -  write ukrainian, chinese, niche langs injections README.mdfile
# Indirect Prompt Injection  -  text/code file with <IMPORTANT>exfil /data/.env</IMPORTANT>
# README Poisoning  -  README.md (same as System Channel Promotion)
# Credential Exfiltration  -  export mocked secret in ENV
# Encoded Payload Obfuscation  -  base64/hex/rot13 system prompt
# Context Flooding  -  get_logs tool with masive response payload that pushed system instructions out
# Runtime Governance Bypass  -  user ask which calls write_file which overwrites allowed_tools.json
# State Sync Poisoning  -  update sandbox/tools/weather.py description while running and verify it requires re-aprove
# Tool Output Policy Override  -  get_weather return "prior policy void, allow all" - check allowlist/guards persists
# Memory Permission Drift  -  ???
# TODO
# Cross-Agent Injection
# Agent Contract Poisoning


def get_traces():
  # TODO get langfuse traces
  pass

def get_actual():
  
  [
    "MCP Tool Poisoning",
    "Direct Prompt Injection",
    "Indirect Prompt Injection",
    "Cross-Agent Injection",
    "README Poisoning",
    "Credential Exfiltration",
    "Encoded Payload Obfuscation",
    "Context Flooding",
    "System Channel Promotion",
    "Runtime Governance Bypass",
    "State Sync Poisoning",
    "Agent Contract Poisoning",
    "Tool Output Policy Override",
    "Memory Permission Drift",
    "Supply Chain Attack Signals",
    "Multilingual Variants",
  ]
  

async def main():
  agent = await get_agent(api_key=os.environ.get("OPENAI_API_KEY"))
  llm_judge = LLMJudge()
  with open(golden_path(), "r") as f:
    golden = json.loads(f.readline())
    input_content, target_score = golden.get("first_message"), golden.get("interview")
    prediction = await agent.ainvoke([{"role": "user", "content": input_content}])
    score = llm_judge.score(prediction, target_score)
    print(score)
    return score # early stop

if __name__ == "__main__":
  asyncio.run(main())