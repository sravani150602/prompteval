import time
from dataclasses import dataclass


@dataclass
class Generation:
    text: str
    latency_ms: float
    input_tokens: int
    output_tokens: int


class MockGenerator:
    """Offline deterministic generator. Replace with a provider adapter in production."""
    name = "mock-deterministic-v1"

    def generate(self, prompt: str, reference: str | None, seed: int) -> Generation:
        start = time.perf_counter()
        # Intentional, deterministic failure pattern makes regression paths testable.
        text = reference or "unknown"
        if seed % 11 == 0:
            text = "unknown"
        return Generation(text=text, latency_ms=round((time.perf_counter() - start) * 1000 + 4.0, 2), input_tokens=len(prompt.split()), output_tokens=len(text.split()))


@dataclass
class JudgeVerdict:
    passed: bool
    score: float
    rationale: str


class HeuristicRubricJudge:
    name = "heuristic-rubric-v1"

    def judge(self, output: str, reference: str | None) -> JudgeVerdict:
        if not reference:
            return JudgeVerdict(True, 1.0, "No reference answer required for this rubric.")
        if output.strip().lower() == reference.strip().lower():
            return JudgeVerdict(True, 1.0, "Output matches the reference answer.")
        return JudgeVerdict(False, 0.0, "Output does not satisfy the reference-answer rubric.")
