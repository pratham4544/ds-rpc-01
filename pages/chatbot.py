# pages/chatbot.py
from src.helper import *
import streamlit as st
import json
import os
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="ChatBot Pro - Chat",
    page_icon="💬",
    layout="wide"
)

# Custom CSS for chat interface
def load_chat_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Chat Container */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        max-height: 500px;
        overflow-y: auto;
    }
    
    /* Message Styles */
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 12px 18px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: 20%;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        word-wrap: break-word;
    }
    
    .bot-message {
        background: #f8f9fa;
        color: #333;
        padding: 12px 18px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    /* Department Header */
    .dept-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .dept-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Source/Context Box */
    .context-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        font-size: 0.9rem;
        color: #6c757d;
    }
    
    .context-title {
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.5rem;
    }
    
    /* Input Area */
    .stChatInput {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem 0;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Button Styles */
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
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Department configurations
dept_configs = {
    "engineering": {
        "icon": "🔧",
        "name": "Engineering Department",
        "color": "#667eea",
        "greeting": "Hello! I'm your Engineering Assistant. I can help with technical questions, development issues, and engineering processes."
    },
    "marketing": {
        "icon": "📈", 
        "name": "Marketing Department",
        "color": "#f093fb",
        "greeting": "Hi there! I'm your Marketing Assistant. I can help with campaigns, brand strategies, and market analysis."
    },
    "finance": {
        "icon": "💰",
        "name": "Finance Department", 
        "color": "#4facfe",
        "greeting": "Welcome! I'm your Finance Assistant. I can help with financial planning, budgets, and analysis."
    },
    "hr": {
        "icon": "👥",
        "name": "Human Resources",
        "color": "#43e97b", 
        "greeting": "Hello! I'm your HR Assistant. I can help with policies, employee relations, and HR processes."
    },
    "general": {
        "icon": "🏢",
        "name": "General Support",
        "color": "#fa709a",
        "greeting": "Hi! I'm your General Assistant. I can help with various inquiries and general support."
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
        st.warning("🔒 Please login first to access the chatbot.")
        st.markdown("[← Go back to login](../)")
        st.stop()
        
    if not st.session_state.get('selected_department'):
        st.warning("🏢 Please select a department first.")
        if st.button("Select Department"):
            st.session_state.selected_department = None
            st.switch_page("main.py")
        st.stop()

def show_department_header(dept_config):
    st.markdown(f"""
    <div class="dept-header">
        <div class="dept-icon">{dept_config['icon']}</div>
        <h2>{dept_config['name']}</h2>
        <p>{dept_config['greeting']}</p>
    </div>
    """, unsafe_allow_html=True)

def display_chat_message(role, content, timestamp=None):
    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            {content}
            {f'<div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">{timestamp}</div>' if timestamp else ''}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="bot-message">
            {content}
            {f'<div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">{timestamp}</div>' if timestamp else ''}
        </div>
        """, unsafe_allow_html=True)

def show_context_sources(context):
    if context:
        st.markdown(f"""
        <div class="context-box">
            <div class="context-title">📚 Sources & Context:</div>
            {context}
        </div>
        """, unsafe_allow_html=True)

# Main function
def main():
    # Load CSS
    load_chat_css()
    
    # Check authentication
    check_auth()
    
    # Get current user and department
    username = st.session_state.get('username')
    selected_department = st.session_state.get('selected_department')
    dept_config = dept_configs.get(selected_department, dept_configs['general'])
    
    # Load user info
    users = load_users()
    user_info = users.get(username, {})
    
    # Sidebar with user info
    with st.sidebar:
        st.markdown("### 👤 User Information")
        st.write(f"**Name:** {user_info.get('full_name', 'N/A')}")
        st.write(f"**Username:** {username}")
        st.write(f"**Email:** {user_info.get('email', 'N/A')}")
        
        st.markdown("---")
        st.markdown("### 🏢 Current Department")
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: {dept_config['color']}20; border-radius: 10px; margin-bottom: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{dept_config['icon']}</div>
            <div style="font-weight: 600;">{dept_config['name']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Change Department", use_container_width=True):
            st.session_state.selected_department = None
            st.switch_page("main.py")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.selected_department = None
            st.switch_page("main.py")
        
        st.markdown("---")
        st.markdown("### 📊 Chat Statistics")
        chat_count = len(st.session_state.get('chat_history', []))
        st.metric("Messages", chat_count)
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # Main content area
    show_department_header(dept_config)
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        # Add welcome message
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": dept_config['greeting'],
            "timestamp": datetime.now().strftime("%I:%M %p")
        })
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history:
        display_chat_message(
            message['role'], 
            message['content'],
            message.get('timestamp')
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    prompt = st.chat_input("💬 Type your message here...")
    
    if prompt:
        # Add user message to chat history
        current_time = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": current_time
        })
        
        # Process the message through your existing chatbot logic
        with st.spinner("🤔 Thinking..."):
            try:
                # Load and process documents (uncomment when ready)
                # docs = load_data_path(path='resources/data')
                # docs_2 = update_metadata_into_docs(docs=docs)
                # vector_store = create_and_store_vs(docs_2)
                
                # Get response from your chatbot (uncomment when ready)
                response, context = answer(question=prompt, input_department=selected_department)
                
                # Temporary response for demonstration
                # response = f"Thank you for your question: '{prompt}'. I'm the {dept_config['name']} assistant. Based on your query, I would typically process this through our specialized knowledge base for the {selected_department} department and provide you with relevant information and solutions."
                # context = f"Knowledge base searched for: {selected_department} department | Query processed at {current_time}"
                
            except Exception as e:
                response = f"I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists."
                context = f"Error: {str(e)}"
        
        # Add bot response to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "context": context
        })
        
        # Rerun to display new messages
        st.rerun()
    
    # Show context for the last bot message if available
    if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'assistant':
        last_message = st.session_state.chat_history[-1]
        if 'context' in last_message and last_message['context']:
            show_context_sources(last_message['context'])

if __name__ == "__main__":
    main()