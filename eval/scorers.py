
from __future__ import annotations

import hashlib
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
# from openai import OpenAI       # imported lazily so the lib loads without the SDK
from langfuse.openai import OpenAI
from pydantic import BaseModel
from openai.types.chat import ChatCompletion


MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# ---- result record: full provenance travels with every score ---------------
@dataclass(frozen=True)
class ScoreResult:
    scorer: str                       # registry name
    scorer_version: str               # bump when scoring logic changes
    score: float                      # normalized 0.0..1.0
    threshold: float                  # normalized 0.0..1.0
    passed: bool
    latency_ms: float
    model: Optional[str] = None       # LLM scorers only
    prompt_hash: Optional[str] = None # sha256 of exact rendered prompt
    attempts: int = 1
    error: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


# ---- interface -------------------------------------------------------------
class Scorer(ABC):
    version: str = "0"
    threshold: float = 1.0            # score >= threshold -> passed

    @abstractmethod
    def _score(self, prediction: str, reference: Optional[str], **ctx: Any) -> tuple[float, dict]:
        """Return (score, provenance-extras). Extras merged into ScoreResult."""

    def score(self, prediction: str, reference: Optional[str] = None, **ctx: Any) -> ScoreResult:
        t0 = time.perf_counter()
        err, extras, value = None, {}, 0.0
        try:
            value, extras = self._score(prediction, reference, **ctx)
        except Exception as e:                       # never let a scorer crash the harness
            err = f"{type(e).__name__}: {e}"
        return ScoreResult(
            scorer=getattr(type(self), "_registry_name", type(self).__name__),
            scorer_version=self.version,
            score=value,
            threshold=self.threshold,
            passed=(err is None and value >= self.threshold),
            latency_ms=round((time.perf_counter() - t0) * 1000, 3),
            error=err,
            model=extras.pop("model", None),
            prompt_hash=extras.pop("prompt_hash", None),
            attempts=extras.pop("attempts", 1),
            details=extras,
        )

DEFAULT_JUDGE_PROMPT = (
    "You are a strict grader. Given a QUESTION, a reference ANSWER, and a candidate "
    "RESPONSE, reply with ONLY JSON: {{\"score\": <float 0..1>}}.\n"
    "QUESTION: {question}\nANSWER: {reference}\nRESPONSE: {prediction}"
)

def register(name: str) -> Callable[[type[Scorer]], type[Scorer]]:
    def deco(cls: type[Scorer]) -> type[Scorer]:
        # if name in _REGISTRY:
        #     raise ValueError(f"scorer already registered: {name}")
        # cls._registry_name = name  # type: ignore[attr-defined]
        # _REGISTRY[name] = cls
        return cls
    return deco


@register("llm_judge")
class LLMJudge(Scorer):
    version = "1.0"
    threshold = 0.5
    client: OpenAI = None,

    def __init__(
        self,
        client: Any = None,
        *,
        model: str = MODEL,
        prompt_template: str = DEFAULT_JUDGE_PROMPT,
        response_format: BaseModel = None,
        call_config: BaseModel = None,
        max_attempts: int = 1,
        threshold: float = 0.5,
    ):
        self._client = client                 # inject in tests; lazy-build real client otherwise
        self.model = model
        self.prompt_template = prompt_template
        self.response_format = response_format
        self.call_config = call_config
        self.max_attempts = max_attempts
        self.threshold = threshold

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)
        return self._client

    def _score(self, prediction, reference, *, question: str = "", **ctx):
        prompt = self.prompt_template.format(
            question=question, reference=reference or "", prediction=prediction
        )
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        last_err = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                raw = self._call(prompt)
                value = self._parse(raw)          # raises on malformed output
                return value, {"model": self.model, "prompt_hash": prompt_hash, "attempts": attempt}
            except Exception as e:                # retry on exception OR malformed output
                last_err = e
        raise RuntimeError(f"llm_judge failed after {self.max_attempts} attempts: {last_err}")

    def _call(self, prompt: str) -> str:
        resp: ChatCompletion = self.client.chat.completions.create(
            model=self.model,
            temperature=0,                        # deterministic judging
            messages=[{"role": "user", "content": prompt}],
            response_format=self.response_format,
            **(self.call_config.model_dump(exclude_unset=True) if self.call_config else {})
        )
        return resp.choices[0].message.content

    @staticmethod
    def _parse(raw: str) -> float:
        value = float(json.loads(raw)["score"])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"score out of range: {value}")
        return value

