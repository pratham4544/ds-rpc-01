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

def get_sample_questions():
    """Return a sample question for each department based on available resources."""
    return [
        {"name": "Engineering", "question": "What is the main technology stack used in our backend services?"},
        {"name": "Finance", "question": "Can you summarize the latest quarterly financial report?"},
        {"name": "HR", "question": "What are the key benefits provided to employees?"},
        {"name": "Marketing", "question": "Show me the highlights from the Q4 2024 marketing report."},
        {"name": "General", "question": "How do I apply for maternity leave?"}
    ]

def main():
    # Check authentication
    check_auth()
    
    # Get current user and department
    username = st.session_state.get('username')
    selected_department = st.session_state.get('selected_department')
    dept_config = dept_configs.get(selected_department, dept_configs['general'])
    
    # Load user info
    users = load_users()
    user_info = users.get(username, {})

    # --- Move Sample Questions to Top of Sidebar ---
    with st.sidebar:
        st.subheader("Sample Questions")
        for sample in get_sample_questions():
            st.markdown(f"**{sample['name']}**: {sample['question']}")
        st.markdown("---")

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.selected_department = None
            st.switch_page("main.py")
        
        st.subheader("Chat Statistics")
        chat_count = len(st.session_state.get('chat_history', []))
        st.write(f"Messages: {chat_count}")
        
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

    # Main content area
    show_department_header(dept_config)
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": dept_config['greeting'],
            "timestamp": datetime.now().strftime("%I:%M %p")
        })
    
    # Display chat history
    for message in st.session_state.chat_history:
        display_chat_message(
            message['role'], 
            message['content'],
            message.get('timestamp')
        )
    
    # Chat input
    prompt = st.chat_input("Type your message here...")
    if prompt:
        current_time = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user", 
            "content": prompt,
            "timestamp": current_time
        })
        with st.spinner("Thinking..."):
            try:
                response, context = answer(question=prompt, input_department=selected_department)
            except Exception as e:
                response = "I apologize, but an error occurred while processing your request."
                context = f"Error: {str(e)}"
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "context": context
        })
        st.rerun()
    
    # Show context for last message if available
    if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'assistant':
        last_message = st.session_state.chat_history[-1]
        if last_message.get('context'):
            show_context_sources(last_message['context'])

if __name__ == "__main__":
    main()