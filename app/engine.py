from statistics import median

from sqlalchemy.orm import Session

from .adapters import HeuristicRubricJudge, MockGenerator
from .config import settings
from .models import Dataset, EvaluationResult, EvaluationRun, PromptVariant


def run_checks(output: str, checks: dict) -> tuple[bool, dict]:
    normalized = output.strip().lower()
    details: dict[str, bool] = {}
    if "exact_match" in checks:
        details["exact_match"] = normalized == str(checks["exact_match"]).strip().lower()
    if "contains_all" in checks:
        details["contains_all"] = all(term.lower() in normalized for term in checks["contains_all"])
    if "contains_none" in checks:
        details["contains_none"] = not any(term.lower() in normalized for term in checks["contains_none"])
    return all(details.values()) if details else True, details


def metrics(results: list[EvaluationResult]) -> dict:
    if not results:
        return {"result_count": 0, "task_pass_rate": 0, "judge_pass_rate": 0, "judge_disagreement_rate": 0, "avg_judge_score": 0, "p50_latency_ms": 0, "p95_latency_ms": 0, "estimated_cost_usd": 0}
    latencies = sorted(r.latency_ms for r in results)
    p95_index = max(0, int(len(latencies) * 0.95 + 0.9999) - 1)
    disagreements = [r for r in results if r.task_passed != r.judge_passed]
    return {
        "result_count": len(results),
        "task_pass_rate": round(sum(r.task_passed for r in results) / len(results), 4),
        "judge_pass_rate": round(sum(r.judge_passed for r in results) / len(results), 4),
        "judge_disagreement_rate": round(len(disagreements) / len(results), 4),
        "avg_judge_score": round(sum(r.judge_score for r in results) / len(results), 4),
        "p50_latency_ms": round(median(latencies), 2),
        "p95_latency_ms": round(latencies[p95_index], 2),
        "estimated_cost_usd": round(sum(r.estimated_cost_usd for r in results), 8),
    }


def execute_run(db: Session, dataset: Dataset, variants: list[PromptVariant], repeats: int, seed: int) -> EvaluationRun:
    generator, judge = MockGenerator(), HeuristicRubricJudge()
    run = EvaluationRun(dataset_id=dataset.id, dataset_version=dataset.version, prompt_variant_ids=[v.id for v in variants], repeats=repeats, seed=seed, evaluator_version=settings.evaluator_version, generator_name=generator.name, status="running")
    db.add(run)
    db.flush()
    for example in dataset.examples:
        for variant in variants:
            for repeat_index in range(repeats):
                rendered = variant.template.format(input=example.input_text)
                generation = generator.generate(rendered, example.reference_answer, seed + example.id + variant.id + repeat_index)
                task_passed, check_details = run_checks(generation.text, example.checks)
                verdict = judge.judge(generation.text, example.reference_answer)
                cost = generation.input_tokens * settings.input_cost_per_million / 1_000_000 + generation.output_tokens * settings.output_cost_per_million / 1_000_000
                db.add(EvaluationResult(run_id=run.id, example_id=example.id, prompt_variant_id=variant.id, repeat_index=repeat_index, rendered_prompt=rendered, output_text=generation.text, task_passed=task_passed, check_details=check_details, judge_passed=verdict.passed, judge_score=verdict.score, judge_rationale=verdict.rationale, latency_ms=generation.latency_ms, input_tokens=generation.input_tokens, output_tokens=generation.output_tokens, estimated_cost_usd=cost))
    run.status = "completed"
    db.commit()
    db.refresh(run)
    return run
