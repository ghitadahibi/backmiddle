from fastapi import APIRouter
from .service import ask_question, QuestionAnswer

router = APIRouter(
    prefix="/qa",
    tags=["Question Answering"]
)

@router.get("/")
def read_root():
    question = "What is the capital of France ?"
    
    return {"question": question, "answer": ask_question(question)}

@router.post("/")
def question_answering(qa: QuestionAnswer):
    return QuestionAnswer(question=qa.question, answer=ask_question(qa.question))