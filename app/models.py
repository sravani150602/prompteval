from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    examples: Mapped[list["Example"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class Example(Base):
    __tablename__ = "examples"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    input_text: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    checks: Mapped[dict] = mapped_column(JSON, default=dict)
    dataset: Mapped[Dataset] = relationship(back_populates="examples")


class PromptVariant(Base):
    __tablename__ = "prompt_variants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    template: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    dataset_version: Mapped[str] = mapped_column(String(80))
    prompt_variant_ids: Mapped[list] = mapped_column(JSON)
    repeats: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int] = mapped_column(Integer)
    evaluator_version: Mapped[str] = mapped_column(String(40))
    generator_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    results: Mapped[list["EvaluationResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    example_id: Mapped[int] = mapped_column(ForeignKey("examples.id"))
    prompt_variant_id: Mapped[int] = mapped_column(ForeignKey("prompt_variants.id"))
    repeat_index: Mapped[int] = mapped_column(Integer)
    rendered_prompt: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    task_passed: Mapped[bool] = mapped_column(Boolean)
    check_details: Mapped[dict] = mapped_column(JSON)
    judge_passed: Mapped[bool] = mapped_column(Boolean)
    judge_score: Mapped[float] = mapped_column(Float)
    judge_rationale: Mapped[str] = mapped_column(Text)
    latency_ms: Mapped[float] = mapped_column(Float)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    estimated_cost_usd: Mapped[float] = mapped_column(Float)
    run: Mapped[EvaluationRun] = relationship(back_populates="results")


class Baseline(Base):
    __tablename__ = "baselines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
