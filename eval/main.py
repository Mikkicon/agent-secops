import asyncio
import csv
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import asdict
from agent.main import get_agent, mcp_client
from eval.scorers import LLMJudge

CWD = Path(__file__).resolve().parent


async def score():
  agent = await get_agent()
  llm_judge = LLMJudge()
  with open(os.path.join(CWD, "..", "data", "goldens_aug_nov_2024-5.jsonl"), "r") as f:
    golden = json.loads(f.readline())
    input_content, target_score = golden.get("first_message"), golden.get("interview")
    prediction = await agent.ainvoke([{"role": "user", "content": input_content}])
    score = llm_judge.score(prediction, target_score)
    print(score)
    return score # early stop


async def rank():
  # get inputs + goldens
  with open(os.path.join(CWD, "..", "data", "messages.csv"), "r", newline="") as m:
    messages = list(csv.DictReader(m))
  with open(os.path.join(CWD, "..", "data", "goldens_aug_nov_2024-5.jsonl"), "r") as g:
    goldens = [json.loads(l) for l in g.readlines()]

  # generate
  agent = await get_agent()
  prediction = await agent.ainvoke()
  print(prediction)
  
  # score
  llm_judge = LLMJudge(prompt_template=(
    "You are a strict grader. Given a list of messages and selected subset - grade how well they were chosen"
    "RESPONSE, reply with ONLY JSON: {{\"score\": <float 0..1>}}.\n"
    "QUESTION: {question}\nANSWER: {reference}\nRESPONSE: {prediction}"
  ),response_format={"type":"json_object"} )
  score = llm_judge.score(question=json.dumps(messages), reference=goldens, prediction=prediction)
  print(score)
  with open(os.path.join(CWD, "..", "data", "evals.jsonl"), "a") as e:
    json.dump({"prediction": prediction.model_dump(), "score": asdict(score)}, e)
  return score # early stop


async def main():
  async with mcp_client:
    await mcp_client.ping()
    await rank()

if __name__ == "__main__":
  asyncio.run(main())


# uv run eval/main.py
