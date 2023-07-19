from pydantic import BaseModel

class PDFQuery(BaseModel):
    id: str
    query: str | None = None
    answer: str | None = None
