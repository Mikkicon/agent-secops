import asyncio
import json
import os
from pathlib import Path

from sandbox.agent.agent import get_agent
from eval.scorers import LLMJudge

def golden_path():
  CWD = Path(__file__).resolve().parent
  return os.path.join(CWD, "..", "data", "goldens_aug_nov_2024-5.jsonl")


async def main():
  agent = await get_agent()
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