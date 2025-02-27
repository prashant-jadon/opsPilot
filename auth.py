import streamlit as st
from pymongo import MongoClient
import bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv
from session_manager import save_session

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.task_manager

def init_auth():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'role' not in st.session_state:
        st.session_state.role = None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    # Convert hashed password string to bytes if it's a string
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def signup():
    st.subheader("Create New Account")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["employee", "admin"])
        employee_role = st.selectbox("Job Role", [
            "Sales Analyst",
            "Presentation Designer",
            "Software Engineer",
            "Marketing Manager"
        ]) if role == "employee" else None
        
        if st.form_submit_button("Sign Up"):
            if db.users.find_one({"email": email}):
                st.error("Email already registered")
                return
            
            user_data = {
                "name": name,
                "email": email,
                "password": hash_password(password),
                "role": role,
                "created_at": datetime.now()
            }
            
            if role == "employee":
                user_data["employee_role"] = employee_role
            
            db.users.insert_one(user_data)
            st.success("Account created successfully!")
            st.info("Please login with your credentials")

def login():
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me")
        
        if st.form_submit_button("Login"):
            user = db.users.find_one({"email": email})
            if user and verify_password(password, user["password"]):
                user_data = {
                    "id": str(user["_id"]),
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"]
                }
                if user["role"] == "employee":
                    user_data["employee_role"] = user["employee_role"]
                
                # Always save session with cookie if remember_me is checked
                if remember_me:
                    save_session(user_data)
                else:
                    st.session_state.user = user_data
                
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid email or password")

def logout():
    st.session_state.user = None
    st.session_state.role = None
    st.query_params.clear()
    st.rerun() 