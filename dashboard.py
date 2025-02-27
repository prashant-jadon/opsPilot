import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from queue import Queue
import threading
from queue_manager import QueueManager

# Load environment variables
load_dotenv()

# Initialize MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.task_manager

def convert_to_datetime(date_str):
    """Convert various date formats to datetime"""
    if pd.isna(date_str) or date_str == 'Not specified':
        return None
    try:
        return pd.to_datetime(date_str)
    except:
        return None

def load_tasks():
    """Load tasks from MongoDB and convert to DataFrame"""
    tasks = list(db.tasks.find())
    if not tasks:
        return pd.DataFrame()
    
    df = pd.DataFrame(tasks)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

def get_queue_status():
    """Get the current queue status"""
    queue_manager = QueueManager()
    return queue_manager.get_status()

def main():
    st.set_page_config(page_title="Task Manager Dashboard", layout="wide")
    
    st.title("📋 Task Manager Dashboard")
    
    # Load data
    df = load_tasks()
    
    if df.empty:
        st.warning("No tasks found in the database")
        return
    
    # Dashboard Layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Task Statistics")
        total_tasks = len(df)
        pending_tasks = len(df[df['status'] == 'pending'])
        
        # Create metrics
        col1a, col1b = st.columns(2)
        with col1a:
            st.metric("Total Tasks", total_tasks)
        with col1b:
            st.metric("Pending Tasks", pending_tasks)
        
        # Tasks by Role pie chart
        tasks_by_role = df['role'].value_counts()
        fig_roles = px.pie(
            values=tasks_by_role.values,
            names=tasks_by_role.index,
            title="Tasks Distribution by Role"
        )
        st.plotly_chart(fig_roles)
        
        # Queue Status
        st.subheader("⚡ Queue Status")
        queue_status = get_queue_status()
        col_queue1, col_queue2 = st.columns(2)
        with col_queue1:
            st.metric("Tasks in Queue", queue_status['queued_tasks'])
        with col_queue2:
            st.metric("Processing Status", "Active" if queue_status['processing'] else "Idle")
    
    with col2:
        st.subheader("📅 Upcoming Deadlines")
        # Filter and convert deadline dates
        df['deadline_date'] = df['deadline'].apply(convert_to_datetime)
        deadline_df = df[df['deadline_date'].notna()].copy()
        
        if not deadline_df.empty:
            deadline_df = deadline_df.sort_values('deadline_date')
            
            fig_timeline = go.Figure(data=[
                go.Scatter(
                    x=deadline_df['deadline_date'],
                    y=deadline_df['task_description'],
                    mode='markers',
                    marker=dict(size=12),
                    text=deadline_df.apply(lambda x: f"{x['assignee_name']} - {x['deadline']}", axis=1)
                )
            ])
            
            fig_timeline.update_layout(
                title="Task Timeline",
                xaxis_title="Deadline",
                yaxis_title="Task",
                height=400
            )
            st.plotly_chart(fig_timeline)
        else:
            st.info("No tasks with valid deadlines found")
    
    # Task List
    st.subheader("📝 Recent Tasks")
    
    # Create task filters
    col_filters1, col_filters2, col_filters3 = st.columns(3)
    
    with col_filters1:
        role_filter = st.multiselect(
            "Filter by Role",
            options=sorted(df['role'].unique())
        )
    
    with col_filters2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=sorted(df['status'].unique())
        )
    
    with col_filters3:
        assignee_filter = st.multiselect(
            "Filter by Assignee",
            options=sorted(df['assignee_name'].unique())
        )
    
    # Apply filters
    filtered_df = df.copy()
    if role_filter:
        filtered_df = filtered_df[filtered_df['role'].isin(role_filter)]
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    if assignee_filter:
        filtered_df = filtered_df[filtered_df['assignee_name'].isin(assignee_filter)]
    
    # Display tasks in an expandable format
    for _, task in filtered_df.sort_values('created_at', ascending=False).iterrows():
        with st.expander(f"{task['task_description']} ({task['status']})"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Assignee:**", task['assignee_name'])
                st.write("**Role:**", task['role'])
            with col2:
                st.write("**Deadline:**", task['deadline'])
                st.write("**Created:**", task['created_at'].strftime('%Y-%m-%d %H:%M'))
            with col3:
                st.write("**Status:**", task['status'])
                # Add status update button
                new_status = st.selectbox(
                    "Update Status",
                    options=['pending', 'in_progress', 'completed'],
                    key=str(task['_id']),
                    index=['pending', 'in_progress', 'completed'].index(task['status'])
                )
                if new_status != task['status']:
                    db.tasks.update_one(
                        {'_id': task['_id']},
                        {'$set': {'status': new_status}}
                    )
                    st.experimental_rerun()
            
            # st.write("**Original Transcript:**", task['original_transcript'])

if __name__ == "__main__":
    main() 