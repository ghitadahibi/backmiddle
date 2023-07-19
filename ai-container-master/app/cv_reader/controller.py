from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from .service import read_cv
from .dto import CVAnalysis

router = APIRouter(
    prefix="/cv-reader",
    tags=["CV Reader"]
)

@router.post("/")
def analyse_cv(
    cv: Annotated[UploadFile, File()]
):
    return read_cv(cv.file)