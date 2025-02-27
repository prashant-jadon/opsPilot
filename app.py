import streamlit as st
from auth import init_auth, signup, login, logout
from admin_view import show_admin_dashboard
from employee_view import show_employee_dashboard
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from database_manager import DatabaseManager
from session_manager import init_session
from config import ThemeConfig as theme

# Set page config first
st.set_page_config(
    page_title="OPSpilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load environment variables
load_dotenv()

# Initialize MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.task_manager

# Initialize session state (this now uses cookies)
init_session()

# Initialize database manager
db_manager = DatabaseManager(db)

def set_page_style():
    st.markdown(
        f"""
        <style>
            .stButton > button {{
                {theme.BUTTON_STYLE.format(color=theme.PRIMARY)}
            }}
            .stButton > button:hover {{
                filter: brightness(1.1);
            }}
            .status-badge {{
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 500;
            }}
            .status-pending {{
                background-color: {theme.BG_WARNING};
                color: {theme.WARNING};
            }}
            .status-in_progress {{
                background-color: {theme.BG_PRIMARY};
                color: {theme.PRIMARY};
            }}
            .status-completed {{
                background-color: {theme.BG_SUCCESS};
                color: {theme.SUCCESS};
            }}
            /* Add more custom styles */
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    set_page_style()
    # Sidebar
    with st.sidebar:
        if st.session_state.user:
            st.write(f"Logged in as: {st.session_state.user['name']}")
            
            # Show notifications
            notifications = list(db.notifications.find({
                "user_id": st.session_state.user["id"],
                "read": False
            }))
            
            if notifications:
                st.warning(f"You have {len(notifications)} unread notifications!")
                with st.expander("View Notifications"):
                    for notif in notifications:
                        st.write(notif['message'])
                        if st.button("Mark as Read", key=str(notif['_id'])):
                            db.notifications.update_one(
                                {"_id": notif['_id']},
                                {"$set": {"read": True}}
                            )
                            st.rerun()
            
            if st.button("Logout"):
                logout()
        else:
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            with tab1:
                login()
            with tab2:
                signup()

    # Main content
    if st.session_state.user:
        if st.session_state.user['role'] == 'admin':
            show_admin_dashboard(db, db_manager)
        else:
            show_employee_dashboard(db, db_manager, st.session_state.user)

if __name__ == "__main__":
    main() 