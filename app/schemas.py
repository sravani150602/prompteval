from pydantic import BaseModel, Field


class ExampleIn(BaseModel):
    input_text: str
    reference_answer: str | None = None
    checks: dict = Field(default_factory=dict)


class DatasetIn(BaseModel):
    name: str
    version: str
    description: str | None = None
    examples: list[ExampleIn] = Field(min_length=1)


class PromptVariantIn(BaseModel):
    name: str
    template: str


class RunIn(BaseModel):
    dataset_id: int
    prompt_variant_ids: list[int] = Field(min_length=1)
    repeats: int = Field(default=3, ge=1, le=10)
    seed: int = 42


class BaselineIn(BaseModel):
    name: str
    run_id: int
