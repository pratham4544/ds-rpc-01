from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
import os
import re
from dotenv import load_dotenv

load_dotenv()  # take environment variables

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

# Load embeddings and LLM
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
llm = GoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GOOGLE_API_KEY)

# Load documents
def load_documents():
    loader = DirectoryLoader('../resources/data')
    docs = loader.load()

    # Update the metadata of documents based on the source file path
    department_list = ['engineering', 'finance', 'hr', 'marketing']
    updated_docs = [
        Document(
            metadata={**doc.metadata, 'department': re.search(r'/data/([^/]+)/', doc.metadata['source']).group(1) if 'general' not in doc.metadata.get('department', '') else department_list},
            page_content=doc.page_content
        )
        for doc in docs
    ]
    return updated_docs

# Initialize vector store
def initialize_vector_store(engineering_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    split_text = text_splitter.split_documents(engineering_data)
    vector_store = FAISS.from_documents(split_text, embedding=embeddings)
    vector_store.save_local("faiss_index")
    return vector_store

# Answer function
def answer(question, input_department):
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    results = new_db.similarity_search(query=question, k=1)
    filtered_results = []

    for doc in results:
        department = doc.metadata.get("department", "")
        source = doc.metadata.get("source", "")
        should_include = False

        if isinstance(department, str):
            if "general" in department.lower() or department.lower() == input_department:
                should_include = True
        elif isinstance(department, list):
            for dept in department:
                if "general" in dept.lower() or dept.lower() == input_department:
                    should_include = True
                    break
        if "general" in source.lower():
            should_include = True

        if should_include:
            filtered_results.append(doc)

    if not filtered_results:
        return "I am sorry, I cannot answer the question as no relevant documents were found."

    context = filtered_results[0].page_content
    prompt = PromptTemplate(template='you are assistant having knowledge of the engineering dept as per question extract the relevent chunks and build answer if you did not find the answer in context say i do not know the answer {question} \\n {context}', input_variables=["context", "question"])
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": context, "question": question})
    return response

# Streamlit application
st.title("Chatbot Application")

# Load documents and initialize vector store
engineering_data = load_documents()
vector_store = initialize_vector_store(engineering_data)

# User input
user_question = st.text_input("Ask a question:")
input_department = st.selectbox("Select your department:", ["engineering", "finance", "hr", "marketing"])

if st.button("Get Answer"):
    if user_question:
        response = answer(user_question, input_department)
        st.write(response)
    else:
        st.write("Please enter a question.")