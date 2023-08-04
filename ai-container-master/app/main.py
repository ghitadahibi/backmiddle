from fastapi import FastAPI, UploadFile, Request, File,Form
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
from cv_reader import controller as cv_reader
from chat_pdf import controller as chat_pdf
import pymongo
from bson.objectid import ObjectId
import pymongo
import re
from bson.objectid import ObjectId
import os
import pymongo
from fastapi import FastAPI, UploadFile, File
from cv_reader import controller as cv_reader
from chat_pdf import controller as chat_pdf
from PyPDF2 import PdfReader
import pymongo
from fastapi import FastAPI, File, UploadFile
import json
from fastapi.responses import JSONResponse
from bson import ObjectId


load_dotenv()
app=FastAPI()





client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
jobmatching_collection = db["jobmatching"]
joboffer_collection = db["joboffers"]
# Route pour récupérer les champs job_name, cv_name et similarity_score de tous les documents de la collection jobmatching
@app.get("/jobmatching")
async def get_jobmatching():
    jobmatching_list = []
    for jobmatching in jobmatching_collection.find({}, {"_id": 0, "job_name": 1, "email": 1, "similarity_score": 1}):
        jobmatching_list.append(jobmatching)
    return jobmatching_list


@app.get("/joboffer")
async def get_jobmatching():
    joboffer_list = []
    for joboffer in joboffer_collection.find({}, {"_id": 0, "jobOfferName": 1, "content": 1}):
        joboffer_list.append(joboffer)
    return joboffer_list



@app.post("/uploadjoboffre")
async def upload_job_offre( joboffre: UploadFile = File(...),joboffre_nom: str = Form(...)):
    if joboffre.content_type == 'application/pdf':
        # Extraire du texte à partir du fichier PDF
        content = await joboffre.read()
        text = ''
        with io.BytesIO(content) as pdf:
            reader = PdfReader(pdf)
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
async def test_match(cv: UploadFile = File(...), job_name: str = Form(...)):
    # Connexion à la base de données MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["mydatabase"]
    collection = db["joboffers"]
    jobmatching_collection = db["jobmatching"]
        
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
        email = re.search(r'Email: (.*)', result).group(1)
               
        
        # Calculer la similarité entre le CV et l'offre d'emploi
        JD_embeddings = get_HF_embeddings([document['content']])
        resume_embeddings = get_HF_embeddings([result])
        similarity_scores = cosine(JD_embeddings, resume_embeddings)
        
        # Insérer le score de similarité et le lien vers le CV dans la collection jobmatching
        jobmatching_collection.insert_one(
            {
                "job_name": job_name,
                "email": email,
                "similarity_score": similarity_scores
            }
        )
        
        return {'Similarity Scores': similarity_scores}
        
    return {'message': 'No job offer found for the given job name.'}

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
joboffer_collection = db["joboffers"]

@app.delete("/deleteall")
async def delete_all_joboffers():
    result = joboffer_collection.delete_many({})
    return {"deleted_count": result.deleted_count}

@app.delete("/joboffers/{jobOfferName}")
async def delete_joboffer(jobOfferName: str):
    result = joboffer_collection.delete_one({"jobOfferName": jobOfferName})
    if result.deleted_count == 1:
        return {"message": f"Job offer with  {jobOfferName} deleted successfully"}
    else:
        return {"message": "Job offer not found"}