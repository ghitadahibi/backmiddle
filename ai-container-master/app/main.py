from fastapi import FastAPI, UploadFile, Request, File
from dotenv import load_dotenv
from models import get_HF_embeddings, cosine
import pdfplumber
from typing import List
import pymongo
import pdfkit
from fastapi.templating import Jinja2Templates
from io import BytesIO
import os
import io
from PyPDF2 import PdfReader
templates = Jinja2Templates(directory="templates")

load_dotenv()
app=FastAPI()

from cv_reader import controller as cv_reader
from chat_pdf import controller as chat_pdf

import pymongo
from bson.objectid import ObjectId

import pymongo
from bson.objectid import ObjectId

import os
import pymongo
from fastapi import FastAPI, UploadFile, File
from cv_reader import controller as cv_reader
from chat_pdf import controller as chat_pdf
from PyPDF2 import PdfReader
import pymongo
from fastapi import FastAPI, File, UploadFile



app = FastAPI()

@app.post("/uploadjoboffre")
async def upload_job_offre(joboffre_nom: str, joboffre: UploadFile = File(...)):
    if joboffre.content_type == 'application/pdf':
        # Lire le contenu du fichier
        content = await joboffre.read()

        # Enregistrer le fichier PDF sur le disque avec le nom donné
        with open(joboffre_nom, 'wb') as f:
            f.write(content)

        # Extraire du texte à partir du fichier PDF
        with open(joboffre_nom, 'rb') as f:
            reader = PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text()

        # Connexion MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["mydatabase"]
        collection = db["joboffers"]

        # Enregistrement du nom du fichier et du contenu dans la collection "joboffers"
        joboffer = {'jobOfferName': joboffre_nom, 'content': text}
        collection.insert_one(joboffer)

        return {'message': 'File uploaded successfully'}


#app.include_router(qa.router)
app.include_router(cv_reader.router)
app.include_router(chat_pdf.router)

@app.post("/testmatching")
async def test_match(job_name: str, cv: UploadFile = File(...)):
        
    # Connexion à la base de données MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["mydatabase"]
    collection = db["joboffers"]
        
    # Requête pour récupérer les offres d'emploi correspondant au nom de poste
    results = collection.find({'jobOfferName': job_name})
    for document in results:
        print("Job Offer Name:", document['jobOfferName'])
        print("Content:", document['content'])
        
        # Extraire du texte à partir du fichier CV
        cv_contents = await cv.read()
        cv_file = io.BytesIO(cv_contents)
        result = cv_reader.read_cv(cv_file)
        print(result)
       
        
        
        # Calculer la similarité entre le CV et l'offre d'emploi
        JD_embeddings = get_HF_embeddings([document['content']])
        resume_embeddings = get_HF_embeddings([result])
        similarity_scores = cosine(JD_embeddings, resume_embeddings)
        return {'Similarity Scores': similarity_scores}
        
    return {'message': 'No job offer found for the given job name.'}

