from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from .service import read_pdf, chat_pdf
from .dto import PDFQuery

router = APIRouter(
    prefix="/chat-pdf",
    tags=["Chat PDF"]
)

@router.post("/")
def index_pdf(
    document: Annotated[UploadFile, File()]
):
    return PDFQuery(id=read_pdf(document.file))

@router.post("/{id}")
def ask_pdf(
    id,
    query: Annotated[str, Form()]
):
    return PDFQuery(id=id, query=query, answer=chat_pdf(id, query))