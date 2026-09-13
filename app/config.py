import os


class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./prompteval.db")
    evaluator_version = os.getenv("EVALUATOR_VERSION", "1.0.0")
    input_cost_per_million = float(os.getenv("INPUT_COST_PER_MILLION", "0.15"))
    output_cost_per_million = float(os.getenv("OUTPUT_COST_PER_MILLION", "0.60"))
    pass_rate_drop_threshold = float(os.getenv("PASS_RATE_DROP_THRESHOLD", "0.02"))
    disagreement_increase_threshold = float(os.getenv("DISAGREEMENT_INCREASE_THRESHOLD", "0.03"))


settings = Settings()
