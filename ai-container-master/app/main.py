from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

#from .qa import controller as qa
from .cv_reader import controller as cv_reader
from .chat_pdf import controller as chat_pdf

app = FastAPI()
#app.include_router(qa.router)
app.include_router(cv_reader.router)
app.include_router(chat_pdf.router)

@app.get("/")
def root():
    return {"message": "Hello from AI Container"}
