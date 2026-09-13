from fastapi import FastAPI

from .api import router
from .db import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="PromptEval", version="0.1.0", description="Reproducible LLM prompt evaluation platform")
app.include_router(router)
