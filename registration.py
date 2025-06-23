# main.py
import streamlit as st
import hashlib
import json
import os
from datetime import datetime
import time
from src.helper import UserManager
from src.helper import load_data_path,update_metadata_into_docs,create_and_store_vs

# Configure page
st.set_page_config(
    page_title="ChatBot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize user manager
user_manager = UserManager()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

def show_header():
    st.title("🤖 ChatBot Pro")
    st.subheader("Your intelligent assistant for all departments")

def show_login_form():
    st.subheader("Login to Your Account")
    
    if st.button('Update Vector DB'):
        docs = load_data_path(path = 'resources/data')
        updated_docs = update_metadata_into_docs(docs)
        db = create_and_store_vs(updated_docs)
        st.success('The Data Is Updated Now')
    # Demo credentials for quick login
    demo_users = [
        {"role": "HR", "username": "HR", "password": "123456"},
        {"role": "Finance", "username": "finance", "password": "123456"},
        {"role": "Marketing", "username": "marketin", "password": "123456"},
        {"role": "Engineering", "username": "engineering", "password": "123456"},
        {"role": "C_Level", "username": "c_level", "password": "123456"},
        
    ]

    demo_cols = st.columns(len(demo_users))
    for i, user in enumerate(demo_users):
        if demo_cols[i].button(f"Login as {user['role']}"):
            st.session_state['demo_username'] = user['username']
            st.session_state['demo_password'] = user['password']
            st.session_state['auto_login'] = True
            st.rerun()

    username_default = st.session_state.get('demo_username', "")
    password_default = st.session_state.get('demo_password', "")

    with st.form("login_form"):
        username = st.text_input("Username", value=username_default, placeholder="Enter your username")
        password = st.text_input("Password", value=password_default, type="password", placeholder="Enter your password")
        col_login, col_register = st.columns(2)
        with col_login:
            login_button = st.form_submit_button("Login")
        with col_register:
            register_button = st.form_submit_button("Register")

        # Auto-login if triggered by demo button
        auto_login = st.session_state.pop('auto_login', False) if 'auto_login' in st.session_state else False
        if login_button or auto_login:
            if username and password:
                success, message = user_manager.authenticate_user(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    user_info = user_manager.get_user_info(username)
                    st.session_state.selected_department = user_info.get('department')
                    st.success("Login successful!")
                    time.sleep(1)
                    st.switch_page('pages/chatbot.py')
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields")

        if register_button:
            st.session_state.show_register = True
            st.rerun()

    # Clear demo credentials after use
    if 'demo_username' in st.session_state:
        del st.session_state['demo_username']
    if 'demo_password' in st.session_state:
        del st.session_state['demo_password']

def show_register_form():
    st.subheader("Create a New Account")
    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="Enter your full name")
        username = st.text_input("Username", placeholder="Choose a username")
        department = st.selectbox("Select your department", ("hr", "finance", "engineering", "marketing",'c_level'))
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        col_create, col_back = st.columns(2)
        with col_create:
            register_button = st.form_submit_button("Create Account")
        with col_back:
            back_button = st.form_submit_button("Back to Login")
        
        if register_button:
            if all([full_name, username, email, password, confirm_password]):
                if password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    success, message = user_manager.register_user(username, department, email, password, full_name)
                    if success:
                        st.success("Registration successful! Please login.")
                        st.session_state.show_register = False
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.error("Please fill in all fields")
        
        if back_button:
            st.session_state.show_register = False
            st.rerun()

def main():
    show_header()
    
    if not st.session_state.authenticated:
        if st.session_state.show_register:
            show_register_form()
        else:
            show_login_form()

if __name__ == "__main__":
    main()