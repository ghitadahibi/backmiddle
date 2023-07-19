from langchain import HuggingFacePipeline, PromptTemplate, LLMChain
from pydantic import BaseModel

class QuestionAnswer(BaseModel):
    question: str
    answer: str | None = None

llm = HuggingFacePipeline.from_model_id(model_id="google/flan-t5-large", task="text2text-generation", model_kwargs={"max_length":100})

def ask_question(question):
    template = """Question: {question}
    
    Answer: Let's think step by step."""
    prompt = PromptTemplate(template=template, input_variables=["question"])
    
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    
    return llm_chain.run(question)
