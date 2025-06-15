from dotenv import load_dotenv
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import DirectoryLoader
import re





load_dotenv()  # take environment variables
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = GOOGLE_API_KEY)


def load_data_path(path = '../resources/data'):
    loader = DirectoryLoader(path)
    docs = loader.load()
    return docs


def update_metadata_into_docs(docs): 
    # Update the metadata of documents based on the source file path
    department_list = ['engineering', 'finance', 'hr', 'marketing']
    updated_docs = []
    for doc in docs:
        source = doc.metadata.get('source', '')
        match = re.search(r'/data/([^/]+)/', source)
        if match:
            dept = match.group(1)
            if dept == 'general':
                # For general documents, give access to all departments
                doc.metadata['department'] = department_list
            else:
                # For specific department documents
                doc.metadata['department'] = dept
            updated_docs.append(doc)
    updated_docs
    return updated_docs


def create_and_store_vs(updated_docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    split_text = text_splitter.split_documents(updated_docs)

    vector_store = FAISS.from_documents(split_text, embedding=embeddings)

    vector_store.save_local("faiss_index")

    return vector_store

def answer(question, input_department):
    # Step 1: Use retriever with the actual question
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 5})
    results = retriever.invoke(question)

    # Step 2: Enhanced filtering to handle both string and list departments
    filtered_results = []
    for doc in results:
        department = doc.metadata.get("department", "")
        source = doc.metadata.get("source", "")
        
        # Check if document should be included based on department
        should_include = False
        
        # Handle case where department is a list
        if isinstance(department, list):
            if "general" in department or input_department in department:
                should_include = True
        # Handle case where department is a string
        elif isinstance(department, str):
            if department.lower() == "general" or department.lower() == input_department.lower():
                should_include = True
        
        # Also check source field for department or general
        if "general" in source.lower() or input_department.lower() in source.lower():
            should_include = True
        
        if should_include:
            filtered_results.append(doc)

    if not filtered_results:
        return "I am sorry, I cannot answer the question as no relevant documents were found.", []

    context = filtered_results
    
    TEMPLATE = '''
    You are a knowledgeable assistant specializing in engineering department information, equipped to provide detailed and contextually relevant answers based on employee inquiries.

    Your task is to extract relevant information from the provided context and construct an accurate response to the question asked. If the necessary information is not found within the context, you will respond with: "I do not know the answer to question"

    Here is the information you will work with:  
    - Question: {question}  
    - Context: {context}  

    ---

    Your response should be clear, concise, and directly address the question based on the context provided. Ensure that your answers reflect the most relevant and accurate information available.

    ---

    Example of a response structure:  
    - If the question is "What are the safety protocols in the engineering department?" and the context includes details about safety procedures, your response should summarize those protocols clearly.  
    - If the question is about a specific engineering project and the context does not provide that information, your response should state: "I do not know the answer to 'What is the status of Project X?'"

    ---

    Be cautious not to include any personal opinions or unverifiable information. Focus solely on factual data derived from the context.
        
    '''
    
    
    prompt = PromptTemplate(template=TEMPLATE, input_variables=["context", "question"])

    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({"context": context, "question": question})
    
    return response, context

