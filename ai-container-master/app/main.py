from fastapi import FastAPI, UploadFile, Request, File
from dotenv import load_dotenv
from models import get_HF_embeddings, cosine
import pdfplumber
from typing import List
import pymongo
import pdfkit
from fastapi.templating import Jinja2Templates
from io import BytesIO

templates = Jinja2Templates(directory="templates")

load_dotenv()

from cv_reader import controller as cv_reader
from chat_pdf import controller as chat_pdf

app = FastAPI()
app.include_router(cv_reader.router)
app.include_router(chat_pdf.router)

@app.get("/")
def root():
    return {"message": "Hello from AI Container"}


@app.post("/compare")
async def compare_resume_to_jd(request: Request, jd_text: UploadFile):
    print(f"Received jd_text: {jd_text.filename}")

    # Connexion MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/cvdata")
    db = client["mydatabase"]
    collection = db["cvs"]

    # Récupération des documents
    documents = collection.find()

    # Generate the list of PDF files to compare
    pdf_files = []
    for doc in documents:
        # Generate PDF from document
        html = templates.TemplateResponse("cv.html", {"request": request, "doc": doc})
        pdf = pdfkit.from_string(html.body.decode('utf-8'), False)
        pdf_files.append(pdf)

    # Get the embeddings of the job description
    if jd_text.content_type == 'application/pdf':
        # If jd_text is a PDF file, extract its text and get its embedding
        with pdfplumber.open(jd_text.file) as pdf:
            pages = pdf.pages
            text = ""
            for page in pages:
                text += page.extract_text()
        jd_embedding = get_HF_embeddings(text)
    else:
        return {'error': 'Invalid job description file type. Only PDF files are accepted.'}

    # Get the embeddings of each PDF file
    file_embeddings = []
    for i, pdf_file in enumerate(pdf_files):
        with BytesIO(pdf_file) as pdf:
            pages = pdfplumber.open(pdf).pages
            text = ""
            for page in pages:
                text += page.extract_text()
            file_embedding = get_HF_embeddings(text)
            file_embeddings.append(file_embedding)

    if not file_embeddings:
        return {'error': 'No PDF files were provided.'}

    # Compute the cosine similarity between the job description and each file's embedding
    similarities = cosine(file_embeddings, jd_embedding)
    # Create a dictionary where the keys are the filenames and the values are their respective cosine similarity scores
    result = {}
    for i, pdf_file in enumerate(pdf_files):
        result[f"file_{i}"] = similarities[i]

    return result