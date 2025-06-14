# RAG-based Role Access Control Chatbot
# Complete Streamlit Application

import streamlit as st
import pandas as pd
import hashlib
import jwt
import datetime
import os
import sqlite3
import json
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
from dataclasses import dataclass
import uuid
import io
from pathlib import Path

# Configuration
st.set_page_config(
    page_title="RAG RBAC Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
SECRET_KEY = "your-secret-key-change-this"
CHROMA_PERSIST_DIR = "./chroma_db"
DATABASE_PATH = "./app_database.db"

# Data Models
@dataclass
class User:
    id: str
    username: str
    email: str
    role: str
    department: str
    created_at: str

@dataclass
class Document:
    id: str
    filename: str
    content: str
    access_level: str
    department: str
    uploaded_by: str
    uploaded_at: str

# Database Management
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                access_level TEXT NOT NULL,
                department TEXT NOT NULL,
                uploaded_by TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            )
        ''')
        
        # Chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin user
        self.create_default_users()
    
    def create_default_users(self):
        """Create default users for testing"""
        default_users = [
            {
                "username": "admin",
                "email": "admin@company.com",
                "password": "admin123",
                "role": "Admin",
                "department": "IT"
            },
            {
                "username": "manager",
                "email": "manager@company.com",
                "password": "manager123",
                "role": "Manager",
                "department": "Sales"
            },
            {
                "username": "employee",
                "email": "employee@company.com",
                "password": "employee123",
                "role": "Employee",
                "department": "Marketing"
            },
            {
                "username": "guest",
                "email": "guest@company.com",
                "password": "guest123",
                "role": "Guest",
                "department": "General"
            }
        ]
        
        for user_data in default_users:
            if not self.get_user_by_username(user_data["username"]):
                self.create_user(
                    user_data["username"],
                    user_data["email"],
                    user_data["password"],
                    user_data["role"],
                    user_data["department"]
                )
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str, role: str, department: str) -> bool:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            created_at = datetime.datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO users (id, username, email, password_hash, role, department, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, role, department, created_at))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return User object"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username, email, role, department, created_at
            FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return User(
                id=result[0],
                username=result[1],
                email=result[2],
                role=result[3],
                department=result[4],
                created_at=result[5]
            )
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, department, created_at
            FROM users
            WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return User(
                id=result[0],
                username=result[1],
                email=result[2],
                role=result[3],
                department=result[4],
                created_at=result[5]
            )
        return None
    
    def save_document(self, filename: str, content: str, access_level: str, department: str, uploaded_by: str) -> str:
        """Save document to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        doc_id = str(uuid.uuid4())
        uploaded_at = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO documents (id, filename, content, access_level, department, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (doc_id, filename, content, access_level, department, uploaded_by, uploaded_at))
        
        conn.commit()
        conn.close()
        return doc_id
    
    def get_accessible_documents(self, user: User) -> List[Document]:
        """Get documents accessible to the user based on their role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user.role == "Admin":
            # Admin can access all documents
            cursor.execute('SELECT * FROM documents')
        elif user.role == "Manager":
            # Manager can access public and department documents
            cursor.execute('''
                SELECT * FROM documents
                WHERE access_level IN ('public', 'department')
                AND (department = ? OR access_level = 'public')
            ''', (user.department,))
        elif user.role == "Employee":
            # Employee can access public documents and their department documents
            cursor.execute('''
                SELECT * FROM documents
                WHERE access_level = 'public'
                OR (access_level = 'department' AND department = ?)
            ''', (user.department,))
        else:  # Guest
            # Guest can only access public documents
            cursor.execute("SELECT * FROM documents WHERE access_level = 'public'")
        
        results = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in results:
            documents.append(Document(
                id=row[0],
                filename=row[1],
                content=row[2],
                access_level=row[3],
                department=row[4],
                uploaded_by=row[5],
                uploaded_at=row[6]
            ))
        
        return documents
    
    def log_audit(self, user_id: str, action: str, resource: str):
        """Log audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        audit_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO audit_logs (id, user_id, action, resource, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (audit_id, user_id, action, resource, timestamp))
        
        conn.commit()
        conn.close()

# RAG System
class RAGSystem:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_document(self, doc_id: str, content: str, metadata: Dict):
        """Add document to vector store"""
        # Split content into chunks
        chunks = self.split_text(content)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            embedding = self.embedding_model.encode(chunk).tolist()
            
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{**metadata, "chunk_id": i, "doc_id": doc_id}]
            )
    
    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def search_documents(self, query: str, user: User, top_k: int = 5) -> List[Dict]:
        """Search for relevant documents based on user permissions"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Create where clause based on user role
        where_clause = self._build_permission_filter(user)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )
        
        return results
    
    def _build_permission_filter(self, user: User) -> Dict:
        """Build permission filter for ChromaDB query"""
        if user.role == "Admin":
            return {}  # No filter, access all
        elif user.role == "Manager":
            return {
                "$or": [
                    {"access_level": "public"},
                    {
                        "$and": [
                            {"access_level": "department"},
                            {"department": user.department}
                        ]
                    }
                ]
            }
        elif user.role == "Employee":
            return {
                "$or": [
                    {"access_level": "public"},
                    {
                        "$and": [
                            {"access_level": "department"},
                            {"department": user.department}
                        ]
                    }
                ]
            }
        else:  # Guest
            return {"access_level": "public"}

# Authentication Manager
class AuthManager:
    def __init__(self):
        self.secret_key = SECRET_KEY
    
    def create_token(self, user: User) -> str:
        """Create JWT token for user"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# Chatbot Response Generator
class ChatbotGenerator:
    def __init__(self):
        self.max_context_length = 4000
    
    def generate_response(self, query: str, context: List[str], user: User) -> str:
        """Generate response using context and query"""
        # Combine context
        combined_context = "\n\n".join(context[:3])  # Use top 3 relevant chunks
        
        # Limit context length
        if len(combined_context) > self.max_context_length:
            combined_context = combined_context[:self.max_context_length] + "..."
        
        # Create prompt
        prompt = f"""
        You are a helpful assistant for {user.username} (Role: {user.role}, Department: {user.department}).
        
        Based on the following context, please answer the user's question. If the context doesn't contain 
        enough information to answer the question, say so politely.
        
        Context:
        {combined_context}
        
        Question: {query}
        
        Answer:
        """
        
        # For demo purposes, return a simulated response
        # In production, you would call OpenAI API or another LLM here
        if context:
            return f"Based on the available documents, here's what I found:\n\n{self._simulate_llm_response(query, combined_context)}"
        else:
            return "I couldn't find relevant information in the documents you have access to. Please check if you have the necessary permissions or try rephrasing your question."
    
    def _simulate_llm_response(self, query: str, context: str) -> str:
        """Simulate LLM response for demo purposes"""
        context_words = context.lower().split()
        query_words = query.lower().split()
        
        # Find common words
        common_words = set(context_words) & set(query_words)
        
        if common_words:
            return f"I found information related to your query about {', '.join(list(common_words)[:3])}. The documents contain relevant details that can help answer your question. The context shows information about these topics in the available documents."
        else:
            return "While I found some potentially relevant documents, they might not directly address your specific question. You may want to try different keywords or contact an administrator for access to additional resources."

# Initialize global objects
@st.cache_resource
def init_app():
    """Initialize application components"""
    db_manager = DatabaseManager(DATABASE_PATH)
    rag_system = RAGSystem()
    auth_manager = AuthManager()
    chatbot = ChatbotGenerator()
    
    return db_manager, rag_system, auth_manager, chatbot

# UI Components
def login_page(auth_manager: AuthManager, db_manager: DatabaseManager):
    """Login page UI"""
    st.title("🤖 RAG RBAC Chatbot")
    st.markdown("### Please login to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                user = db_manager.authenticate_user(username, password)
                if user:
                    token = auth_manager.create_token(user)
                    st.session_state.token = token
                    st.session_state.user = user
                    db_manager.log_audit(user.id, "login", "system")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.markdown("**Demo Accounts:**")
        st.markdown("• Admin: `admin` / `admin123`")
        st.markdown("• Manager: `manager` / `manager123`")
        st.markdown("• Employee: `employee` / `employee123`")
        st.markdown("• Guest: `guest` / `guest123`")

def sidebar_navigation(user: User):
    """Sidebar navigation"""
    st.sidebar.title(f"Welcome, {user.username}!")
    st.sidebar.markdown(f"**Role:** {user.role}")
    st.sidebar.markdown(f"**Department:** {user.department}")
    
    st.sidebar.markdown("---")
    
    # Navigation options based on role
    pages = ["💬 Chat", "📁 Documents"]
    
    if user.role in ["Admin", "Manager"]:
        pages.append("📤 Upload Documents")
    
    if user.role == "Admin":
        pages.extend(["👥 User Management", "📊 Analytics"])
    
    selected_page = st.sidebar.selectbox("Navigate to:", pages)
    
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    return selected_page

def chat_page(user: User, rag_system: RAGSystem, chatbot: ChatbotGenerator, db_manager: DatabaseManager):
    """Chat interface"""
    st.title("💬 Chat with Documents")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                # Search for relevant documents
                search_results = rag_system.search_documents(prompt, user)
                
                # Extract context
                context = []
                if search_results and search_results['documents']:
                    context = search_results['documents'][0]  # Get first batch of results
                
                # Generate response
                response = chatbot.generate_response(prompt, context, user)
                st.markdown(response)
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                # Log interaction
                db_manager.log_audit(user.id, "chat_query", prompt)

def documents_page(user: User, db_manager: DatabaseManager):
    """Documents management page"""
    st.title("📁 Document Library")
    
    # Get accessible documents
    documents = db_manager.get_accessible_documents(user)
    
    if documents:
        st.markdown(f"You have access to **{len(documents)}** documents:")
        
        # Create a table of documents
        doc_data = []
        for doc in documents:
            doc_data.append({
                "Filename": doc.filename,
                "Access Level": doc.access_level,
                "Department": doc.department,
                "Uploaded By": doc.uploaded_by,
                "Uploaded At": doc.uploaded_at.split('T')[0]  # Just the date
            })
        
        df = pd.DataFrame(doc_data)
        st.dataframe(df, use_container_width=True)
        
        # Document viewer
        st.markdown("---")
        st.subheader("Document Viewer")
        
        selected_doc = st.selectbox(
            "Select a document to view:",
            options=[doc.filename for doc in documents],
            index=0 if documents else None
        )
        
        if selected_doc:
            doc = next(doc for doc in documents if doc.filename == selected_doc)
            st.text_area(
                "Document Content:",
                doc.content,
                height=300,
                disabled=True
            )
    else:
        st.info("No documents are accessible with your current permissions.")

def upload_page(user: User, db_manager: DatabaseManager, rag_system: RAGSystem):
    """Document upload page"""
    st.title("📤 Upload Documents")
    
    if user.role not in ["Admin", "Manager"]:
        st.error("You don't have permission to upload documents.")
        return
    
    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'docx'])
        
        col1, col2 = st.columns(2)
        with col1:
            access_level = st.selectbox(
                "Access Level:",
                ["public", "department", "restricted"] if user.role == "Admin" else ["public", "department"]
            )
        
        with col2:
            department = st.selectbox(
                "Department:",
                ["General", "IT", "Sales", "Marketing", "HR", "Finance"]
            )
        
        submit_button = st.form_submit_button("Upload Document", use_container_width=True)
        
        if submit_button and uploaded_file:
            # Read file content
            content = ""
            if uploaded_file.type == "text/plain":
                content = str(uploaded_file.read(), "utf-8")
            else:
                # For demo, treat all files as text
                content = str(uploaded_file.read(), "utf-8", errors='ignore')
            
            # Save to database
            doc_id = db_manager.save_document(
                uploaded_file.name,
                content,
                access_level,
                department,
                user.username
            )
            
            # Add to vector store
            metadata = {
                "filename": uploaded_file.name,
                "access_level": access_level,
                "department": department,
                "uploaded_by": user.username
            }
            rag_system.add_document(doc_id, content, metadata)
            
            # Log action
            db_manager.log_audit(user.id, "document_upload", uploaded_file.name)
            
            st.success(f"Document '{uploaded_file.name}' uploaded successfully!")

def admin_page(user: User, db_manager: DatabaseManager):
    """Admin management page"""
    if user.role != "Admin":
        st.error("Access denied. Admin privileges required.")
        return
    
    st.title("👥 User Management")
    
    tab1, tab2 = st.tabs(["Create User", "View Users"])
    
    with tab1:
        st.subheader("Create New User")
        with st.form("create_user_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["Admin", "Manager", "Employee", "Guest"])
            new_department = st.selectbox("Department", ["IT", "Sales", "Marketing", "HR", "Finance", "General"])
            
            if st.form_submit_button("Create User"):
                if db_manager.create_user(new_username, new_email, new_password, new_role, new_department):
                    st.success(f"User '{new_username}' created successfully!")
                    db_manager.log_audit(user.id, "user_creation", new_username)
                else:
                    st.error("Failed to create user. Username or email might already exist.")
    
    with tab2:
        st.subheader("Existing Users")
        # This would require additional database methods to implement fully
        st.info("User listing functionality would be implemented here.")

def analytics_page(user: User, db_manager: DatabaseManager):
    """Analytics dashboard"""
    if user.role != "Admin":
        st.error("Access denied. Admin privileges required.")
        return
    
    st.title("📊 Analytics Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", "4")  # Would be dynamic in real implementation
    
    with col2:
        st.metric("Total Documents", "0")  # Would be dynamic
    
    with col3:
        st.metric("Chat Sessions", "0")  # Would be dynamic
    
    with col4:
        st.metric("Active Users", "1")  # Would be dynamic
    
    st.markdown("---")
    st.info("Detailed analytics would be implemented here with charts and graphs.")

# Main Application
def main():
    # Initialize app components
    db_manager, rag_system, auth_manager, chatbot = init_app()
    
    # Check authentication
    if "token" not in st.session_state or "user" not in st.session_state:
        login_page(auth_manager, db_manager)
        return
    
    # Verify token
    token_data = auth_manager.verify_token(st.session_state.token)
    if not token_data:
        st.error("Session expired. Please login again.")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        return
    
    user = st.session_state.user
    
    # Show sidebar navigation
    selected_page = sidebar_navigation(user)
    
    # Route to appropriate page
    if selected_page == "💬 Chat":
        chat_page(user, rag_system, chatbot, db_manager)
    elif selected_page == "📁 Documents":
        documents_page(user, db_manager)
    elif selected_page == "📤 Upload Documents":
        upload_page(user, db_manager, rag_system)
    elif selected_page == "👥 User Management":
        admin_page(user, db_manager)
    elif selected_page == "📊 Analytics":
        analytics_page(user, db_manager)

if __name__ == "__main__":
    main()