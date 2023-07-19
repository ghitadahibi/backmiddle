from pydantic import BaseModel

class CVAnalysis(BaseModel):
    summary: str
    answer: str | None = None
