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
import streamlit as st
import os
import json
from datetime import datetime
import hashlib
from src.prompt import RBC


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
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 7})
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
    
    TEMPLATE = RBC    
    prompt = PromptTemplate(template=TEMPLATE, input_variables=["context", "question", 'department'])

    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({"context": context, "question": question, 'department':input_department})
    
    return response, context


# User database operations
class UserManager:
    def __init__(self, db_file="users.json"):
        self.db_file = db_file
        self.users = self.load_users()
    
    def load_users(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_users(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, department, email, password, full_name):
        if username in self.users:
            return False, "Username already exists"
        if any(user.get('email') == email for user in self.users.values()):
            return False, "Email already registered"
        
        self.users[username] = {
            'email': email,
            'department': department,
            'password': self.hash_password(password),
            'full_name': full_name,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.save_users()
        return True, "Registration successful"
    
    def authenticate_user(self, username, password):
        if username not in self.users:
            return False, "User not found"
        
        if self.users[username]['password'] != self.hash_password(password):
            return False, "Invalid password"
        
        # Update last login timestamp
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.save_users()
        return True, "Login successful"
    
    def get_user_info(self, username):
        return self.users.get(username, {})


# Department configurations
dept_configs = {
    "engineering": {
        "icon": "🔧",
        "name": "Engineering Department",
        "greeting": "Hello! I'm your Engineering Assistant. I can help with technical questions and development issues."
    },
    "marketing": {
        "icon": "📈", 
        "name": "Marketing Department",
        "greeting": "Hi there! I'm your Marketing Assistant. I can help with campaigns and market analysis."
    },
    "finance": {
        "icon": "💰",
        "name": "Finance Department", 
        "greeting": "Welcome! I'm your Finance Assistant. I can help with financial planning and analysis."
    },
    "hr": {
        "icon": "👥",
        "name": "Human Resources",
        "greeting": "Hello! I'm your HR Assistant. I can help with employee relations and HR processes."
    },
    "general": {
        "icon": "🏢",
        "name": "General Support",
        "greeting": "Hi! I'm your General Assistant. I can help with various inquiries and support."
    }
}

# Load user database
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", 'r') as f:
            return json.load(f)
    return {}

# Check authentication
def check_auth():
    if not st.session_state.get('authenticated', False):
        st.warning("Please login first to access the chatbot.")
        st.markdown("[← Go back to login](../)")
        st.stop()
        
    if not st.session_state.get('selected_department'):
        st.warning("Please select a department first.")
        if st.button("Select Department"):
            st.session_state.selected_department = None
            st.switch_page("main.py")
        st.stop()

def show_department_header(dept_config):
    st.header(dept_config['name'])
    st.write(dept_config['greeting'])

def display_chat_message(role, content, timestamp=None):
    ts = f" [{timestamp}]" if timestamp else ""
    if role == "user":
        st.markdown(f"**User:** {content}{ts}")
    else:
        st.markdown(f"**Assistant:** {content}{ts}")

def show_context_sources(context):
    if context:
        st.info(f"Sources & Context: {context}")