from app.db import SessionLocal
from app.engine import execute_run, metrics
from app.models import Dataset, PromptVariant
from app.seed import seed

seed()
db = SessionLocal()
dataset = db.query(Dataset).filter_by(name="support-intent-heldout").one()
variants = db.query(PromptVariant).all()
run = execute_run(db, dataset, variants, repeats=3, seed=42)
print("## PromptEval smoke evaluation")
for key, value in metrics(run.results).items():
    print(f"- **{key}**: {value}")
