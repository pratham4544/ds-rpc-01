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



class SessionManager:
    """Manage user sessions and chat history"""
    
    @staticmethod
    def save_chat_session(username, department, chat_history):
        """Save chat session to file"""
        session_dir = "chat_sessions"
        os.makedirs(session_dir, exist_ok=True)
        
        session_file = f"{session_dir}/{username}_{department}_{datetime.now().strftime('%Y%m%d')}.json"
        
        session_data = {
            "username": username,
            "department": department,
            "timestamp": datetime.now().isoformat(),
            "chat_history": chat_history
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    @staticmethod
    def load_chat_session(username, department):
        """Load previous chat session"""
        session_dir = "chat_sessions"
        session_file = f"{session_dir}/{username}_{department}_{datetime.now().strftime('%Y%m%d')}.json"
        
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                return session_data.get('chat_history', [])
        
        return []

class DatabaseManager:
    """Enhanced database operations"""
    
    def __init__(self, db_file="enhanced_users.json"):
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
    
    def create_user(self, username, email, password, full_name, department_preferences=None):
        """Create a new user with enhanced profile"""
        if username in self.users:
            return False, "Username already exists"
        
        if any(user.get('email') == email for user in self.users.values()):
            return False, "Email already registered"
        
        self.users[username] = {
            'email': email,
            'password': self.hash_password(password),
            'full_name': full_name,
            'department_preferences': department_preferences or [],
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'login_count': 0,
            'chat_sessions': [],
            'profile_settings': {
                'theme': 'default',
                'notifications': True,
                'auto_save_chats': True
            }
        }
        self.save_users()
        return True, "Registration successful"
    
    def authenticate_user(self, username, password):
        """Authenticate user and update login stats"""
        if username not in self.users:
            return False, "User not found"
        
        if self.users[username]['password'] != self.hash_password(password):
            return False, "Invalid password"
        
        # Update login stats
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.users[username]['login_count'] = self.users[username].get('login_count', 0) + 1
        self.save_users()
        return True, "Login successful"
    
    def update_user_preferences(self, username, preferences):
        """Update user preferences"""
        if username in self.users:
            self.users[username]['profile_settings'].update(preferences)
            self.save_users()
            return True
        return False
    
    def log_chat_session(self, username, department, message_count):
        """Log chat session for analytics"""
        if username in self.users:
            session_log = {
                'department': department,
                'timestamp': datetime.now().isoformat(),
                'message_count': message_count
            }
            
            if 'chat_sessions' not in self.users[username]:
                self.users[username]['chat_sessions'] = []
            
            self.users[username]['chat_sessions'].append(session_log)
            self.save_users()

class AnalyticsManager:
    """Analytics and reporting for the chatbot"""
    
    @staticmethod
    def get_user_stats(username, users_db):
        """Get user statistics"""
        if username not in users_db:
            return {}
        
        user_data = users_db[username]
        chat_sessions = user_data.get('chat_sessions', [])
        
        stats = {
            'total_sessions': len(chat_sessions),
            'total_messages': sum(session.get('message_count', 0) for session in chat_sessions),
            'favorite_department': None,
            'last_active': user_data.get('last_login'),
            'member_since': user_data.get('created_at')
        }
        
        # Find favorite department
        if chat_sessions:
            dept_counts = {}
            for session in chat_sessions:
                dept = session.get('department', 'unknown')
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            stats['favorite_department'] = max(dept_counts, key=dept_counts.get)
        
        return stats
    
    @staticmethod
    def get_department_stats(department, users_db):
        """Get department usage statistics"""
        total_sessions = 0
        total_messages = 0
        unique_users = set()
        
        for username, user_data in users_db.items():
            chat_sessions = user_data.get('chat_sessions', [])
            for session in chat_sessions:
                if session.get('department') == department:
                    total_sessions += 1
                    total_messages += session.get('message_count', 0)
                    unique_users.add(username)
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'unique_users': len(unique_users)
        }

def validate_email(email):
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Password validation with requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return "Unknown"

def export_chat_history(chat_history, username, department):
    """Export chat history to JSON format"""
    export_data = {
        "user": username,
        "department": department,
        "export_date": datetime.now().isoformat(),
        "chat_history": chat_history
    }
    
    return json.dumps(export_data, indent=2)

# Streamlit utility functions
def show_success_message(message, duration=3):
    """Show success message with auto-hide"""
    success_placeholder = st.empty()
    success_placeholder.success(message)
    
def show_error_message(message, duration=3):
    """Show error message with auto-hide"""
    error_placeholder = st.empty()
    error_placeholder.error(message)

def create_download_link(data, filename, link_text):
    """Create download link for data"""
    import base64
    
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">{link_text}</a>'
    return href