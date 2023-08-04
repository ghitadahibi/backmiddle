from pypdf import PdfReader
import re
import json
import pymongo

from langchain import HuggingFacePipeline
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI
from langchain.vectorstores import FAISS

def format_to_json(input_string):

    pattern = r'\b[A-Z][a-z0-9]*'
    matches = re.findall(pattern, input_string)
    camelcase_matches = [match.lower() if idx == 0 else match.capitalize() for idx, match in enumerate(matches)]
    data = {}
    for i in range(len(camelcase_matches)):
        if i + 1 < len(camelcase_matches) and ':' in input_string:
            key = camelcase_matches[i].strip(':')
            value = camelcase_matches[i + 1]
            data[key] = value
    json_data = json.dumps(data, indent=2)
    return json_data

def transform_string_to_json(input_string):
    lines = input_string.split('\n')
    data = {}
    for line in lines:
        parts = line.split(':')
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            data[key] = value
    json_data = json.dumps(data, indent=4)
    return json_data

def format_string_to_json(text):
    print(text)
    text = text.replace('\n\n', '\n')
    print(text)
    lines = text.split('\n')
    json_data = {}
    for line in lines:
        if line.strip() != '':
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key.startswith('Questions'):
                    if key not in json_data:
                        json_data[key] = []
                    json_data[key].append(value)
                else:
                    json_data[key] = value
            else:
                key = parts[0].strip()
                value = ''
                json_data[key] = value
    json_output = json.dumps(json_data, indent=4)
    return json_output

def texte_en_json(texte):
    # Créer un dictionnaire vide pour stocker les informations
    data = {}

    # Diviser le texte en sections en utilisant le mot-clé "Questions"
    sections = texte.split('Questions')

    # Parcourir chaque section du texte
    for section in sections:
        # Diviser la section en lignes
        lignes = section.split('\n')

        # Vérifier si la section contient des questions
        if len(lignes) > 1:
            # Récupérer le type de questions (soft skills ou techniques)
            type_questions = lignes[0].strip()

            # Créer une liste vide pour stocker les questions
            questions = []

            # Parcourir chaque ligne de la section (sauf la première ligne)
            for ligne in lignes[1:]:
                # Vérifier si la ligne est vide
                if ligne.strip() == '':
                    continue

                # Ajouter la question à la liste
                questions.append(ligne.strip())

            # Ajouter les questions au dictionnaire principal
            data[type_questions] = questions
        else:
            # Diviser la ligne en clé et valeur en utilisant le premier ':' comme séparateur
            index = section.index(':')
            cle = section[:index].strip()
            valeur = section[index+1:].strip()

            # Ajouter la paire clé-valeur au dictionnaire principal
            data[cle] = valeur
    
    print(data)
    
    # Convertir le dictionnaire en format JSON et le renvoyer
    return data

def text_to_array(text, key):
    #print(text + ':' + key)
    return text
    questions = text.split('. ')
    if len(questions) == 1:
        return text
    print(text)
    data = []

    for question in questions:
        question = question.strip()
        if question != '':
            question_number, question_text = question.split('. ', 1)
            question_number = int(question_number.strip())
            question_text = question_text.strip()
            data.append({question_number: question_text})

    #json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return data

def text_to_data(text):
    lines = text.split('\n')
    data = {}
    current_key = ''

    for line in lines:
        if line.strip() != '':
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key in data:
                    if isinstance(data[key], list):
                        data[key].append(value)
                    else:
                        print(data[key])
                        data[key] = [data[key], value]
                else:
                    data[key] = value
                current_key = key
            else:
                print(line)
                if (line.endswith('?')):
                    if current_key in data:
                        if isinstance(data[current_key], list):
                            data[current_key].append(line.strip())
                        else:
                            data[current_key] = [line.strip()]
                    else:
                        data[current_key] = line.strip()
                else:
                    data[current_key] += line.strip()

    #json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return data

def read_cv_openai(cv):
    reader = PdfReader(cv)
    docs = [
        Document(
            page_content=page.extract_text(),
            metadata={"page": i},
        )
        for i, page in enumerate(reader.pages)
    ]
    
    prompt_template = """En tant que responsable de recrutement dans une entreprise marocaine, utilisez le contexte suivant pour répondre aux questions à la fin.
    Si vous ne connaisser pas la réponse, répondre par Inconnu, n'essayez pas de fournir une réponse.

    {context}

    Questions : {questions}
    
    Réponses aux questions les suivants : 
    Titre: """

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "questions"]
    )
    
    llm = OpenAI()

    chain = load_qa_chain(llm, chain_type="stuff",  prompt=PROMPT)

    query = [
        "Une briève présentation du profil ! Titre:",
        "Quel est le nom complèt ? Nom complét:",
        "Quel est le type de la formation la plus récente ? Niveau des études:",
        "Dans quelle institution le candidat a poursuit ses études les plus récentes ? Institution:",
        "Quelle sont les domaines d'expertise ? Technologies et domaines d'expertise:",
        "Dans quelle entreprise il a passé l'expérience la plus récente  ? Entreprise:",
        "Quelle est l'intitulé du poste ? Dernier poste:",
        "Quel est le nombre total d'années d'expérience professionnelle ? Années d'expérience:",
        "Quelle est la ville de résidence ? Ville de résidence:",
        "Quelle est votre email ? Email"
    ]
    
    summary = chain.run(input_documents=docs, questions=query)
    
    return summary

def text_to_db(text):
    lines = text.split('\n')
    data = {}
    current_key = ''

    for line in lines:
        if line.strip() != '':
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if '[' in value and ']' in value:
                    # Parse array values
                    value = value[1:-1].split(',')

                    # Strip whitespace from individual values
                    value = [item.strip() for item in value]

                if key in data:
                    if isinstance(data[key], list):
                        data[key].append(value)
                    else:
                        data[key] = [data[key], value]
                else:
                    data[key] = value
                current_key = key
            else:
                data[current_key] += ' ' + line.strip()

    #json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return data
def test():
    text = """Titre: Ingénieur Fullstack Java-React Senior
    Nom complét:  Yousra Oufrid
    Niveau des études:  Ingénieur d'Etat en Génie Logiciel
    Institution:  Ecole Nationale des Sciences Appliquées de Marrakech (ENSA-M)
    Technologies et domaines d'expertise:  Spring 5.3, JPA 2.0, JSP, JSTL, EJB 3.1, Struts 1.3, Play2, SWING, JDBC, Java, C, NSDK, C++, Shell, Matlab, Pascal, Prolog, SQL, PL/SQL, PYTHON, ReactJS, Redux, HTML 5, CSS3, LESS, JavaScript, Eclipse, NetBeans, IntelliJ IDEA, Dev C++, Code Blocks, ORACLE 10g, MySQL, PosgreSQL, UML2, Design Patterns, Merise 2, Power AMC, StarUML, Linux, Windows XP, Windows 7, Windows 8, Windows 10, MS-DOS, Architectures TCP/IP et OSI, VLAN, Safe, Sc
Résumé:
Yousra Oufrid est un ingénieur fullstack Java-React senior possédant des compétences solides en technologies Java/JEE, langages de programmation, technologies web, EDI, bases de données, méthodes d'analyse et de conception et ateliers de génie logiciel.
Questions en soft skills:
1. Quels sont les projets qui vous ont le plus motivé(e) à ce jour?
2. Comment décririez-vous vos principales qualités de travail d'équipe?
3. Quels processus mettez-vous en place pour garantir la qualité de vos produits?
Questions techniques:
1. Quels sont les technologies que vous utilisez actuellement?
2. Quelle est votre expérience avec les systèmes d'exploitation et les protocoles réseau?
3. Quels processus de développement agile utilisez-vous?
"""
    myclient = pymongo.MongoClient("mongodb://localhost:27017")
    mydb = myclient["mydatabase"]
    mycol = mydb["cvs"]
    mycol.insert_one(text_to_data(text))
    return text

def read_cv(cv):
    reader = PdfReader(cv)
    pages = [
        Document(
            page_content=page.extract_text(),
            metadata={"page": i},
        )
        for i, page in enumerate(reader.pages)
    ]
    
    llm = OpenAI(max_tokens=512)

    prompt_template = """En tant que responsable de recrutement dans une entreprise marocaine, utilisez le contexte suivant pour répondre aux questions à la fin.
    Si vous ne connaisser pas la réponse, répondre par Inconnu, n'essayez pas de fournir une réponse.

    {context}

    Questions : {questions}
    
    Réponses aux questions les suivants en format JSON : 
    Titre: """

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "questions"]
    )
    
    chain = load_qa_chain(llm, chain_type="stuff",  prompt=PROMPT)

    query = [
        "Une briève présentation du profil ! Titre:",
        "Quel est le nom complèt ? Nom complét:",
        "Quel est le type de la formation la plus récente ? Niveau des études:",
        "Dans quelle institution le candidat a poursuit ses études les plus récentes ? Institution:",
        "Quelle sont les domaines d'expertise ? Technologies et domaines d'expertise:",
        "Dans quelle entreprise il a passé l'expérience la plus récente  ? Entreprise:",
        "Quelle est l'intitulé du poste ? Dernier poste:",
        "Quel est le nombre total d'années d'expérience professionnelle ? Années d'expérience:",
        "Quelle est la ville de résidence ? Ville de résidence:",
        "Quelle votre email ? Email:"
    ]
    
    result = chain.run(input_documents=pages, questions=query)

    domaines = "SQL, ReactJS, React Native, Spring"

    prompt_template = """En tant que responsable de recrutement dans une entreprise marocaine, écrire un résumé bref du profil en une phrase et puis proposer trois questions en soft skills et trois questions techniques.

    {text}

    Formatter la réponse en format JSON
    Résumé: """

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["text"]
    )
    
    chain = load_summarize_chain(llm, chain_type="stuff",  prompt=PROMPT)

    summary = chain.run(input_documents=pages)

    response = "Titre:" + result + "\nRésumé:" + summary
    myclient = pymongo.MongoClient("mongodb://localhost:27017")
    mydb = myclient["mydatabase"]
    mycol = mydb["cvs"]
    mycol.insert_one(text_to_data(response))
    return response

def read_cv_free(cv):
    reader = PdfReader(cv)
    raw_text = ''
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            raw_text += text
    
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap = 200,
        length_function= len
    )
    docs = text_splitter.split_text(raw_text)
    
    embeddings = HuggingFaceEmbeddings()
    
    db = FAISS.from_texts(docs, embeddings)

    llm = HuggingFacePipeline.from_model_id(model_id="google/flan-t5-xl", task="text2text-generation", model_kwargs={"temperature": 0, "max_length":512})
    
    chain = load_qa_chain(llm, chain_type="stuff")

    response = ''

    query = "Quel est le nom complèt ?"
    response += "/nNom Complét : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Quel est le type de la formation la plus récente ?"
    response += "\nNiveau des études : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Dans quelle institution le candidat a poursuit ses études les plus récentes ?"
    response += "\nInstitution : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Quelle sont les domaines d'expertise ?"
    response += "\nTechnologies et domaines d'expertise : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Dans quelle entreprise il a passé l'expérience la plus récente ?"
    response += "\nEntreprise : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Quelle est l'intitulé du poste ?"
    response += "\nDernier poste : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Quel est le nombre total d'années d'expérience professionnelle ?"
    response += "\nAnnées d'expérience : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Quelle est la ville de résidence ?"
    response += "\nVille de résidence : "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)

    query = "Quelle est votre email ?"
    response += "\nEmail: "
    docs = db.similarity_search(query)
    response += chain.run(input_documents=docs, question=query)


    return response