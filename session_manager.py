import streamlit as st
import jwt
import datetime
from datetime import timedelta
import os
from dotenv import load_dotenv
import extra_streamlit_components as stx

load_dotenv()

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

def get_cookie_manager():
    """Get or create a cookie manager instance"""
    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="unique_cookie_key")
    return st.session_state.cookie_manager

def create_session_token(user_data):
    """Create a JWT token for the user session"""
    expiration = datetime.datetime.utcnow() + timedelta(days=7)
    token = jwt.encode(
        {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'exp': expiration
        },
        SECRET_KEY,
        algorithm='HS256'
    )
    return token

def validate_session_token(token):
    """Validate the JWT token and return user data if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def init_session():
    """Initialize or restore the session"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Initialize cookie manager if not exists
    cookie_manager = get_cookie_manager()
    
    # Try to get token from cookies
    cookies = cookie_manager.get_all()
    token = cookies.get('session_token')
    
    if token and not st.session_state.user:
        user_data = validate_session_token(token)
        if user_data:
            restore_session(user_data)
        else:
            # Clear invalid token
            cookie_manager.delete(cookie='session_token')

def restore_session(user_data):
    """Restore user session from token data"""
    from database_manager import DatabaseManager
    from pymongo import MongoClient
    
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client.task_manager
    db_manager = DatabaseManager(db)
    
    user = db_manager.get_user_by_id(user_data['user_id'])
    if user:
        st.session_state.user = {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
        if user["role"] == "employee":
            st.session_state.user["employee_role"] = user["employee_role"]

def save_session(user_data):
    """Save session data and set cookie"""
    token = create_session_token(user_data)
    st.session_state.user = user_data
    
    # Set cookie with token
    cookie_manager = get_cookie_manager()
    expiry = datetime.datetime.now() + timedelta(days=7)
    
    cookie_manager.set(
        cookie='session_token',
        val=token,
        expires_at=expiry
    )

def logout():
    """Clear session and cookie"""
    cookie_manager = get_cookie_manager()
    cookie_manager.delete(cookie='session_token')
    st.session_state.user = None
    st.session_state.role = None
    st.rerun() 