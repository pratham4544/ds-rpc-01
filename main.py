# main.py
import streamlit as st
import hashlib
import json
import os
from datetime import datetime
import time

# Configure page
st.set_page_config(
    page_title="ChatBot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
def load_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Auth Container */
    .auth-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    
    /* Profile Card */
    .profile-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
    }
    
    .profile-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .profile-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .profile-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        margin-right: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: white;
    }
    
    .profile-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
    }
    
    .profile-dept {
        color: #7f8c8d;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Department Colors */
    .engineering { background: linear-gradient(135deg, #667eea, #764ba2); }
    .marketing { background: linear-gradient(135deg, #f093fb, #f5576c); }
    .finance { background: linear-gradient(135deg, #4facfe, #00f2fe); }
    .hr { background: linear-gradient(135deg, #43e97b, #38f9d7); }
    .general { background: linear-gradient(135deg, #fa709a, #fee140); }
    
    /* Custom Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Success/Error Messages */
    .success-message {
        background: linear-gradient(135deg, #43e97b, #38f9d7);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 500;
    }
    
    .error-message {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 500;
    }
    
    /* Sidebar Styles */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .css-1d391kg .css-1v0mbdj {
        color: white;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

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
    
    def register_user(self, username, email, password, full_name):
        if username in self.users:
            return False, "Username already exists"
        
        if any(user.get('email') == email for user in self.users.values()):
            return False, "Email already registered"
        
        self.users[username] = {
            'email': email,
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
        
        # Update last login
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.save_users()
        return True, "Login successful"
    
    def get_user_info(self, username):
        return self.users.get(username, {})

# Initialize user manager
user_manager = UserManager()

# Sample data for account profiles
profiles = [
    {
        "icon": "🔧",
        "department": "engineering",
        "name": "Engineering Department",
        "description": "Technical support and development queries"
    },
    {
        "icon": "📈",
        "department": "marketing",
        "name": "Marketing Department", 
        "description": "Brand, campaigns, and market analysis"
    },
    {
        "icon": "💰",
        "department": "finance",
        "name": "Finance Department",
        "description": "Financial planning and analysis"
    },
    {
        "icon": "👥",
        "department": "hr",
        "name": "Human Resources",
        "description": "Employee relations and policies"
    },
    {
        "icon": "🏢",
        "department": "general",
        "name": "General Support",
        "description": "General inquiries and support"
    }
]

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Load custom CSS
load_css()

def show_header():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 ChatBot Pro</h1>
        <p>Your intelligent assistant for all departments</p>
    </div>
    """, unsafe_allow_html=True)

def show_login_form():
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_login, col_register = st.columns(2)
            
            with col_login:
                login_button = st.form_submit_button("Login", use_container_width=True)
            
            with col_register:
                register_button = st.form_submit_button("Register", use_container_width=True)
            
            if login_button:
                if username and password:
                    success, message = user_manager.authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("Login successful! 🎉")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please fill in all fields")
            
            if register_button:
                st.session_state.show_register = True
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_register_form():
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 📝 Create New Account")
        
        with st.form("register_form"):
            full_name = st.text_input("Full Name", placeholder="Enter your full name")
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            col_register, col_back = st.columns(2)
            
            with col_register:
                register_button = st.form_submit_button("Create Account", use_container_width=True)
            
            with col_back:
                back_button = st.form_submit_button("Back to Login", use_container_width=True)
            
            if register_button:
                if all([full_name, username, email, password, confirm_password]):
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        success, message = user_manager.register_user(username, email, password, full_name)
                        if success:
                            st.success("Registration successful! Please login. 🎉")
                            st.session_state.show_register = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("Please fill in all fields")
            
            if back_button:
                st.session_state.show_register = False
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_profile_selection():
    # User info in sidebar
    with st.sidebar:
        user_info = user_manager.get_user_info(st.session_state.username)
        st.markdown("### 👤 User Profile")
        st.write(f"**Name:** {user_info.get('full_name', 'N/A')}")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Email:** {user_info.get('email', 'N/A')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.selected_department = None
            st.rerun()
    
    st.markdown("### 🏢 Select Department")
    st.markdown("Choose the department you'd like to chat with:")
    
    # Create responsive grid
    cols = st.columns(2)
    
    for i, profile in enumerate(profiles):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="profile-card" onclick="selectProfile('{profile['department']}')">
                <div class="profile-header">
                    <div class="profile-icon {profile['department']}">
                        {profile['icon']}
                    </div>
                    <div>
                        <h3 class="profile-name">{profile['name']}</h3>
                        <p class="profile-dept">{profile['department']}</p>
                    </div>
                </div>
                <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{profile['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select {profile['name']}", key=f"select_{profile['department']}", use_container_width=True):
                st.session_state.selected_department = profile['department']
                st.success(f"✅ Selected {profile['name']}")
                time.sleep(1)
                st.switch_page('pages/chatbot.py')
                st.rerun()
                

def show_chatbot_interface():
    # User info and department in sidebar
    with st.sidebar:
        user_info = user_manager.get_user_info(st.session_state.username)
        st.markdown("### 👤 User Profile")
        st.write(f"**Name:** {user_info.get('full_name', 'N/A')}")
        st.write(f"**Username:** {st.session_state.username}")
        
        st.markdown("### 🏢 Current Department")
        selected_profile = next((p for p in profiles if p['department'] == st.session_state.selected_department), None)
        if selected_profile:
            st.markdown(f"""
            <div class="profile-icon {selected_profile['department']}" style="margin: 0 auto; margin-bottom: 10px;">
                {selected_profile['icon']}
            </div>
            """, unsafe_allow_html=True)
            st.write(f"**{selected_profile['name']}**")
        
        if st.button("🔄 Change Department", use_container_width=True):
            st.session_state.selected_department = None
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.selected_department = None
            st.rerun()
    
    # Main chat interface
    st.markdown(f"### 💬 Chat with {selected_profile['name'] if selected_profile else 'Department'}")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"""
                <div style="text-align: right; margin: 10px 0;">
                    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 70%;">
                        {message['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: left; margin: 10px 0;">
                    <div style="background: #f1f3f4; color: #333; padding: 10px 15px; border-radius: 15px; display: inline-block; max-width: 70%;">
                        {message['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    prompt = st.chat_input("Type your message here...")
    
    if prompt:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Simulate bot response (replace with your actual chatbot logic)
        response = f"Thank you for your message about '{prompt}'. I'm the {st.session_state.selected_department} department assistant. How can I help you further?"
        
        # Add bot response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()

# Main application logic
def main():
    show_header()
    
    if not st.session_state.authenticated:
        if st.session_state.show_register:
            show_register_form()
        else:
            show_login_form()
    else:
        if st.session_state.selected_department:
            show_chatbot_interface()
        else:
            show_profile_selection()

if __name__ == "__main__":
    main()