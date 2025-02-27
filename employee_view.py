import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_calendar import calendar
import json
from task_chat import TaskChat, show_chat_interface
from calendar_view import show_calendar
from config import ThemeConfig as theme

def show_employee_dashboard(db, db_manager, user):
    # Initialize chat history if not exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Modern welcome header with user info
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(120deg, {theme.PRIMARY}, {theme.SECONDARY});
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div>
                <h1 style="margin: 0;">Welcome back, {user['name']} 👋</h1>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{user['employee_role']}</p>
            </div>
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 1rem;
                border-radius: 8px;
                backdrop-filter: blur(10px);
            ">
                <div style="font-size: 0.9rem; opacity: 0.9;">{user['email']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Get employee's tasks using db_manager
    tasks = db_manager.get_user_tasks(user["id"])
    if not tasks:
        st.info("No tasks assigned yet")
        return
        
    df = pd.DataFrame(tasks)
    
    # Task Statistics with modern cards
    st.markdown("### 📊 Task Overview")
    stats_cols = st.columns(4)
    with stats_cols[0]:
        total_tasks = len(df)
        st.markdown(
            f"""
            <div style="background-color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 600; color: #7C3AED;">{total_tasks}</div>
                <div style="color: #6B7280;">Total Tasks</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with stats_cols[1]:
        pending = len(df[df['status'] == 'pending'])
        st.markdown(
            f"""
            <div style="background-color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 600; color: #D97706;">{pending}</div>
                <div style="color: #6B7280;">Pending</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with stats_cols[2]:
        in_progress = len(df[df['status'] == 'in_progress'])
        st.markdown(
            f"""
            <div style="background-color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 600; color: #4F46E5;">{in_progress}</div>
                <div style="color: #6B7280;">In Progress</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with stats_cols[3]:
        completed = len(df[df['status'] == 'completed'])
        st.markdown(
            f"""
            <div style="background-color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <div style="font-size: 2rem; font-weight: 600; color: #059669;">{completed}</div>
                <div style="color: #6B7280;">Completed</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Add calendar view after stats
    show_calendar(tasks, user_role="employee")

    # Task List and Chat Tabs
    st.markdown("### 📝 Tasks & Chat")
    main_tabs = st.tabs(["All Tasks", "Pending", "In Progress", "Completed", "💬 Task Chat"])
    
    # Initialize task chat
    task_chat = TaskChat(db_manager)
    
    # First 4 tabs for task lists
    for tab_index, (tab, status) in enumerate(zip(main_tabs[:4], ["all", "pending", "in_progress", "completed"])):
        with tab:
            filtered_df = df if status == "all" else df[df['status'] == status]
            for idx, task in filtered_df.sort_values('created_at', ascending=False).iterrows():
                with st.expander(f"{task['task_description']}", expanded=False):
                    cols = st.columns([2, 1])
                    with cols[0]:
                        st.markdown(
                            f"""
                            <div style="margin-bottom: 0.5rem;">
                                <span class="status-badge status-{task['status']}">{task['status'].replace('_', ' ').title()}</span>
                            </div>
                            <div style="color: #374151; margin-bottom: 0.5rem;">
                                <strong>Deadline:</strong> {task['deadline']}
                            </div>
                            <div style="color: #6B7280; font-size: 0.875rem;">
                                Created: {task['created_at'].strftime('%Y-%m-%d %H:%M')}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with cols[1]:
                        select_key = f"status_{tab_index}_{task['_id']}_{status}"
                        new_status = st.selectbox(
                            "Update Status",
                            options=['pending', 'in_progress', 'completed'],
                            key=select_key,
                            index=['pending', 'in_progress', 'completed'].index(task['status'])
                        )
                        if new_status != task['status']:
                            button_key = f"save_{tab_index}_{task['_id']}_{status}"
                            if st.button("Save", key=button_key, type="primary"):
                                update_task_status(task, new_status, db_manager, user)
    
    # Chat tab
    with main_tabs[4]:
        st.markdown(
            """
            <div style="background-color: #F3F4F6; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #374151;">💬 Task Assistant</h4>
                <p style="margin: 0.5rem 0 0 0; color: #6B7280; font-size: 0.875rem;">
                    Ask about any of your tasks - I have context for all of them
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Display current tasks summary
        with st.expander("Your Current Tasks", expanded=True):
            for task in tasks:
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.5rem; padding: 0.5rem; background-color: white; border-radius: 4px;">
                        <div style="color: #374151; font-weight: 500;">{task['task_description']}</div>
                        <div style="color: #6B7280; font-size: 0.875rem;">
                            Status: {task['status'].replace('_', ' ').title()} | 
                            Deadline: {task['deadline']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(msg['user'])
            with st.chat_message("assistant"):
                st.write(msg['assistant'])
        
        # Chat input
        message = st.chat_input("Ask about your tasks...")
        if message:
            # Pass all tasks as context
            response = task_chat.chat(
                message=message,
                task_id=None,  # No specific task
                user={
                    **user,
                    'tasks': tasks  # Include all tasks in user context
                }
            )

def get_status_color(status):
    colors = {
        'pending': '#FFA500',
        'in_progress': '#4169E1',
        'completed': '#32CD32'
    }
    return colors.get(status, '#808080')

def update_task_status(task, new_status, db_manager, user):
    """Helper function to update task status"""
    if db_manager.update_task(task['_id'], {'status': new_status}):
        notification_data = {
            'user_id': user['id'],
            'task_id': str(task['_id']),
            'message': f"Task '{task['task_description']}' status updated to {new_status}",
            'type': 'status_update'
        }
        db_manager.create_notification(notification_data)
        st.rerun()
    else:
        st.error("Failed to update task status") 