from .db import Base, SessionLocal, engine
from .models import Dataset, Example, PromptVariant


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(Dataset).filter_by(name="support-intent-heldout").first():
        dataset = Dataset(name="support-intent-heldout", version="sample-1", description="Tiny frozen demo fixture")
        dataset.examples = [Example(input_text="I was charged twice", reference_answer="billing", checks={"exact_match":"billing"}), Example(input_text="My package has not arrived", reference_answer="shipping", checks={"exact_match":"shipping"}), Example(input_text="I cannot reset my password", reference_answer="account", checks={"exact_match":"account"})]
        db.add(dataset)
    for name, template in [("concise-v1", "Classify in one word: {input}"), ("concise-v2", "Return only the support intent for: {input}"), ("structured-v3", "Input: {input}\\nIntent:")]:
        if not db.query(PromptVariant).filter_by(name=name).first(): db.add(PromptVariant(name=name, template=template))
    db.commit(); db.close()


if __name__ == "__main__": seed()
