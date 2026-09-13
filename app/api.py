from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .engine import execute_run, metrics
from .models import Baseline, Dataset, EvaluationRun, PromptVariant
from .schemas import BaselineIn, DatasetIn, PromptVariantIn, RunIn

router = APIRouter()


def run_payload(run: EvaluationRun) -> dict:
    return {"id": run.id, "status": run.status, "dataset_id": run.dataset_id, "dataset_version": run.dataset_version, "prompt_variant_ids": run.prompt_variant_ids, "repeats": run.repeats, "seed": run.seed, "generator_name": run.generator_name, "evaluator_version": run.evaluator_version, "created_at": run.created_at.isoformat(), "metrics": metrics(run.results)}


@router.get("/health")
def health():
    return {"status": "ok", "evaluator_version": settings.evaluator_version}


@router.post("/datasets", status_code=201)
def create_dataset(payload: DatasetIn, db: Session = Depends(get_db)):
    dataset = Dataset(name=payload.name, version=payload.version, description=payload.description)
    dataset.examples = [__import__("app.models", fromlist=["Example"]).Example(input_text=e.input_text, reference_answer=e.reference_answer, checks=e.checks) for e in payload.examples]
    db.add(dataset); db.commit(); db.refresh(dataset)
    return {"id": dataset.id, "name": dataset.name, "version": dataset.version, "example_count": len(dataset.examples)}


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    return [{"id": d.id, "name": d.name, "version": d.version, "example_count": len(d.examples)} for d in db.query(Dataset).all()]


@router.post("/prompt-variants", status_code=201)
def create_variant(payload: PromptVariantIn, db: Session = Depends(get_db)):
    if db.query(PromptVariant).filter_by(name=payload.name).first():
        raise HTTPException(409, "Prompt variant name already exists")
    variant = PromptVariant(**payload.model_dump()); db.add(variant); db.commit(); db.refresh(variant)
    return {"id": variant.id, "name": variant.name, "template": variant.template}


@router.get("/prompt-variants")
def list_variants(db: Session = Depends(get_db)):
    return [{"id": v.id, "name": v.name, "template": v.template} for v in db.query(PromptVariant).all()]


@router.post("/runs", status_code=201)
def create_run(payload: RunIn, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, payload.dataset_id)
    if not dataset: raise HTTPException(404, "Dataset not found")
    variants = db.query(PromptVariant).filter(PromptVariant.id.in_(payload.prompt_variant_ids)).all()
    if len(variants) != len(set(payload.prompt_variant_ids)): raise HTTPException(404, "One or more prompt variants not found")
    return run_payload(execute_run(db, dataset, variants, payload.repeats, payload.seed))


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(EvaluationRun, run_id)
    if not run: raise HTTPException(404, "Run not found")
    return run_payload(run)


@router.post("/baselines", status_code=201)
def create_baseline(payload: BaselineIn, db: Session = Depends(get_db)):
    if not db.get(EvaluationRun, payload.run_id): raise HTTPException(404, "Run not found")
    existing = db.query(Baseline).filter_by(name=payload.name).first()
    if existing: existing.run_id = payload.run_id; baseline = existing
    else: baseline = Baseline(**payload.model_dump()); db.add(baseline)
    db.commit(); return {"name": baseline.name, "run_id": baseline.run_id}


@router.get("/runs/{run_id}/regression")
def regression(run_id: int, baseline_name: str, db: Session = Depends(get_db)):
    candidate = db.get(EvaluationRun, run_id); baseline = db.query(Baseline).filter_by(name=baseline_name).first()
    if not candidate or not baseline: raise HTTPException(404, "Run or baseline not found")
    base_run = db.get(EvaluationRun, baseline.run_id); current, prior = metrics(candidate.results), metrics(base_run.results)
    pass_delta = round(current["task_pass_rate"] - prior["task_pass_rate"], 4)
    disagreement_delta = round(current["judge_disagreement_rate"] - prior["judge_disagreement_rate"], 4)
    passed = pass_delta >= -settings.pass_rate_drop_threshold and disagreement_delta <= settings.disagreement_increase_threshold
    return {"baseline_name": baseline_name, "baseline_run_id": base_run.id, "candidate_run_id": candidate.id, "task_pass_rate_delta": pass_delta, "judge_disagreement_rate_delta": disagreement_delta, "passed": passed, "thresholds": {"max_pass_rate_drop": settings.pass_rate_drop_threshold, "max_disagreement_increase": settings.disagreement_increase_threshold}}


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard(db: Session = Depends(get_db)):
    latest = db.query(EvaluationRun).order_by(EvaluationRun.id.desc()).first()
    value = metrics(latest.results) if latest else {"result_count": 0, "task_pass_rate": 0, "judge_disagreement_rate": 0, "p95_latency_ms": 0, "estimated_cost_usd": 0}
    cards = [("RESULTS", value["result_count"]), ("TASK PASS RATE", f'{value["task_pass_rate"]:.1%}'), ("JUDGE DISAGREEMENT", f'{value["judge_disagreement_rate"]:.1%}'), ("P95 LATENCY", f'{value["p95_latency_ms"]:.2f} ms'), ("EST. COST", f'${value["estimated_cost_usd"]:.6f}')]
    card_html = ''.join(f'<article><span>{k}</span><strong>{v}</strong></article>' for k,v in cards)
    return f'''<!doctype html><html><head><title>PromptEval</title><style>body{{margin:0;background:#0c1222;color:#e6edf7;font-family:Inter,Arial,sans-serif}}main{{max-width:1000px;margin:0 auto;padding:52px 26px}}.tag{{color:#7dd3fc;text-transform:uppercase;letter-spacing:.16em;font-size:12px}}h1{{font-size:44px;margin:12px 0}}p{{color:#aab8cf;line-height:1.5}}section{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:32px 0}}article{{background:#151e35;border:1px solid #2a3858;border-radius:12px;padding:20px}}span{{display:block;font-size:11px;color:#8fa2c4;letter-spacing:.08em}}strong{{font-size:24px;display:block;margin-top:12px}}.panel{{background:#151e35;border:1px solid #2a3858;border-radius:12px;padding:24px}}code{{color:#a5f3fc}}@media(max-width:720px){{section{{grid-template-columns:1fr 1fr}}}}</style></head><body><main><div class="tag">LLM evaluation platform</div><h1>PromptEval</h1><p>Reproducible prompt comparison with task checks, rubric judging, and regression gates.</p><section>{card_html}</section><div class="panel"><h2>Latest run</h2><p>{'No evaluation run yet. Seed the fixture, then create a run through <code>/docs</code>.' if not latest else f'Run #{latest.id} . dataset v{latest.dataset_version} . {latest.repeats} repeats . {latest.generator_name}'}</p><p>Use <code>/docs</code> to create datasets, register prompt variants, execute runs, and compare a candidate against a baseline.</p></div></main></body></html>'''
