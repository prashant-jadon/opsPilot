import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from auth import hash_password  # Import the hash_password function
from task_chat import TaskChat, show_chat_interface
from calendar_view import show_calendar
from config import ThemeConfig as theme

def get_dashboard_stats(db):
    """Get dashboard statistics from the database"""
    try:
        # Get all tasks
        tasks = pd.DataFrame(list(db.tasks.find()))
        employees = pd.DataFrame(list(db.users.find({"role": "employee"})))
        
        # Calculate stats
        stats = {
            'total_tasks': len(tasks) if not tasks.empty else 0,
            'active_employees': len(employees) if not employees.empty else 0,
            'completion_rate': 0,
            'tasks_this_week': 0
        }
        
        if not tasks.empty:
            # Calculate completion rate
            completed_tasks = len(tasks[tasks['status'] == 'completed'])
            stats['completion_rate'] = (completed_tasks / len(tasks)) * 100 if len(tasks) > 0 else 0
            
            # Calculate tasks created this week
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday())
            tasks['created_at'] = pd.to_datetime(tasks['created_at'])
            stats['tasks_this_week'] = len(tasks[tasks['created_at'] >= week_start])
        
        return stats
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        return {
            'total_tasks': 0,
            'active_employees': 0,
            'completion_rate': 0,
            'tasks_this_week': 0
        }

def show_admin_dashboard(db, db_manager):
    # Modern header with gradient background
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(120deg, {theme.PRIMARY}, {theme.SECONDARY});
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            color: white;
        ">
            <h1 style="margin: 0;">OpsPilot Dashboard ⚡</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Welcome to your command center</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Quick stats in modern cards
    stats = get_dashboard_stats(db)
    cols = st.columns(4)
    
    stats_data = [
        {
            "label": "Total Tasks", 
            "value": stats['total_tasks'],
            "color": theme.PRIMARY,
            "bg_color": theme.BG_PRIMARY,
            "icon": "📊"
        },
        {
            "label": "Active Employees", 
            "value": stats['active_employees'],
            "color": theme.SECONDARY,
            "bg_color": theme.BG_SECONDARY,
            "icon": "👥"
        },
        {
            "label": "Completion Rate", 
            "value": f"{stats['completion_rate']:.1f}%",
            "color": theme.SUCCESS,
            "bg_color": theme.BG_SUCCESS,
            "icon": "✨"
        },
        {
            "label": "Tasks This Week", 
            "value": stats['tasks_this_week'],
            "color": theme.WARNING,
            "bg_color": theme.BG_WARNING,
            "icon": "📅"
        }
    ]
    
    for col, stat in zip(cols, stats_data):
        with col:
            st.markdown(
                f"""
                <div style="background-color: {stat['bg_color']}; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid {stat['color']}20;">
                    <div style="font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem;">{stat['icon']}</div>
                    <div style="font-size: 2rem; font-weight: 600; color: {stat['color']}; text-align: center; margin-bottom: 0.5rem;">
                        {stat['value']}
                    </div>
                    <div style="color: #4B5563; text-align: center; font-size: 0.9rem; font-weight: 500;">
                        {stat['label']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Add calendar view after stats
    tasks = list(db.tasks.find())
    show_calendar(tasks, user_role="admin")

    # Modern tabs for different sections
    tabs = st.tabs(["📈 Overview", "👥 Team", "📝 Tasks", "🔔 Notifications", "💬 Chat"])
    
    with tabs[0]:
        show_overview_charts(db)
    
    with tabs[1]:
        manage_employees(db_manager, db)
    
    with tabs[2]:
        manage_tasks(db, db_manager)
    
    with tabs[3]:
        manage_notifications(db, db_manager)
    
    with tabs[4]:
        task_chat = TaskChat(db_manager)
        show_chat_interface(task_chat, user={"role": "admin"})

def show_overview_charts(db):
    """Show overview charts and statistics"""
    try:
        tasks = pd.DataFrame(list(db.tasks.find()))
        if not tasks.empty:
            # Task Status Distribution
            st.markdown("### Task Status Distribution")
            status_counts = tasks['status'].value_counts()
            fig1 = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                hole=0.6,
                color_discrete_sequence=['#7C3AED', '#4F46E5', '#059669']
            )
            fig1.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=0, l=0, r=0, b=0),
                height=300
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Tasks by Role
            st.markdown("### Tasks by Role")
            role_counts = tasks['role'].value_counts()
            fig2 = px.bar(
                x=role_counts.index,
                y=role_counts.values,
                color_discrete_sequence=['#7C3AED']
            )
            fig2.update_layout(
                xaxis_title="Role",
                yaxis_title="Number of Tasks",
                showlegend=False,
                margin=dict(t=0, l=0, r=0, b=0),
                height=300
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Task Timeline
            st.markdown("### Task Timeline")
            tasks['created_at'] = pd.to_datetime(tasks['created_at'])
            timeline_data = tasks.groupby([tasks['created_at'].dt.date, 'status']).size().reset_index()
            timeline_data.columns = ['date', 'status', 'count']
            
            fig3 = px.line(
                timeline_data,
                x='date',
                y='count',
                color='status',
                color_discrete_map={
                    'pending': '#D97706',
                    'in_progress': '#4F46E5',
                    'completed': '#059669'
                }
            )
            fig3.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Tasks",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=30, l=0, r=0, b=0),
                height=300
            )
            st.plotly_chart(fig3, use_container_width=True)
            
        else:
            st.info("No tasks available to display statistics")
            
    except Exception as e:
        st.error(f"Error displaying overview charts: {str(e)}")

def manage_employees(db_manager, db):
    st.subheader("Employee Management")
    
    # Add new employee
    with st.expander("Add New Employee"):
        with st.form("add_employee"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Job Role", [
                "Sales Analyst",
                "Presentation Designer",
                "Software Engineer",
                "Marketing Manager"
            ])
            
            if st.form_submit_button("Add Employee"):
                if db_manager.get_user(email):
                    st.error("Email already registered")
                else:
                    employee_data = {
                        "name": name,
                        "email": email,
                        "password": hash_password(password),
                        "role": "employee",
                        "employee_role": role,
                        "created_at": datetime.now()
                    }
                    if db_manager.create_user(employee_data):
                        st.success("Employee added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add employee")

    # List and manage employees
    employees = list(db.users.find({"role": "employee"}))
    if employees:
        df = pd.DataFrame([{
            'Name': emp['name'],
            'Email': emp['email'],
            'Job Role': emp.get('employee_role', 'Not Set'),
            'Created': emp['created_at'].strftime('%Y-%m-%d %H:%M') if 'created_at' in emp else 'Unknown',
            'ID': str(emp['_id'])
        } for emp in employees])
        
        st.dataframe(
            df.drop('ID', axis=1),
            column_config={
                'Name': st.column_config.TextColumn('Name'),
                'Email': st.column_config.TextColumn('Email'),
                'Job Role': st.column_config.TextColumn('Job Role'),
                'Created': st.column_config.TextColumn('Created')
            },
            hide_index=True
        )

        # Employee management actions
        st.subheader("Employee Actions")
        selected_emp_id = st.selectbox(
            "Select Employee",
            options=df['ID'].tolist(),
            format_func=lambda x: df[df['ID'] == x]['Name'].iloc[0]
        )

        if selected_emp_id:
            with st.expander("Manage Employee"):
                col1, col2 = st.columns(2)
                with col1:
                    new_role = st.selectbox(
                        "Update Role",
                        options=[
                            "Sales Analyst",
                            "Presentation Designer",
                            "Software Engineer",
                            "Marketing Manager"
                        ]
                    )
                    if st.button("Update Role"):
                        if db_manager.update_user(selected_emp_id, {"employee_role": new_role}):
                            st.success("Role updated successfully")
                            st.rerun()
                        else:
                            st.error("Failed to update role")

                with col2:
                    if st.button("Delete Employee", type="primary"):
                        if st.checkbox("Confirm deletion"):
                            if db_manager.delete_user(selected_emp_id):
                                st.success("Employee deleted successfully")
                                st.rerun()
                            else:
                                st.error("Failed to delete employee")

def manage_tasks(db, db_manager):
    st.subheader("Task Management")
    
    tasks = pd.DataFrame(list(db.tasks.find()))
    if not tasks.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            role_filter = st.multiselect(
                "Filter by Role",
                options=sorted(tasks['role'].unique())
            )
        with col2:
            status_filter = st.multiselect(
                "Filter by Status",
                options=sorted(tasks['status'].unique())
            )
        with col3:
            assignee_filter = st.multiselect(
                "Filter by Assignee",
                options=sorted(tasks['assignee_name'].unique())
            )
        
        # Apply filters
        filtered_df = tasks.copy()
        if role_filter:
            filtered_df = filtered_df[filtered_df['role'].isin(role_filter)]
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
        if assignee_filter:
            filtered_df = filtered_df[filtered_df['assignee_name'].isin(assignee_filter)]
        
        # Display tasks
        for _, task in filtered_df.sort_values('created_at', ascending=False).iterrows():
            with st.expander(f"{task['task_description']} ({task['status']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Assignee:**", task['assignee_name'])
                    st.write("**Role:**", task['role'])
                    
                    # Add deadline update functionality
                    current_deadline = pd.to_datetime(task['deadline']) if task['deadline'] != 'Not specified' else None
                    new_deadline = st.date_input(
                        "Update Deadline",
                        value=current_deadline,
                        key=f"deadline_{task['_id']}"
                    )
                    
                    if new_deadline != current_deadline:
                        if st.button("Update Deadline", key=f"update_deadline_{task['_id']}"):
                            if db_manager.update_task(task['_id'], {'deadline': new_deadline.strftime('%Y-%m-%d')}):
                                # Create notification for the assignee
                                notification_data = {
                                    'user_id': task['assignee_id'],
                                    'task_id': str(task['_id']),
                                    'message': f"Deadline for task '{task['task_description']}' has been updated to {new_deadline.strftime('%Y-%m-%d')}",
                                    'type': 'deadline_update'
                                }
                                db_manager.create_notification(notification_data)
                                st.success("Deadline updated successfully")
                                st.rerun()
                            else:
                                st.error("Failed to update deadline")
                
                with col2:
                    new_status = st.selectbox(
                        "Update Status",
                        options=['pending', 'in_progress', 'completed'],
                        key=str(task['_id']),
                        index=['pending', 'in_progress', 'completed'].index(task['status'])
                    )
                    if new_status != task['status']:
                        if db_manager.update_task(task['_id'], {'status': new_status}):
                            notification_data = {
                                'user_id': task['assignee_id'],
                                'task_id': str(task['_id']),
                                'message': f"Your task '{task['task_description']}' status was updated to {new_status}",
                                'type': 'status_update'
                            }
                            db_manager.create_notification(notification_data)
                            st.rerun()
                        else:
                            st.error("Failed to update task status")

def manage_notifications(db, db_manager):
    st.subheader("Notification Management")
    
    # Create new notification
    with st.expander("Send New Notification"):
        with st.form("send_notification"):
            recipients = st.multiselect(
                "Select Recipients",
                options=list(db.users.find({"role": "employee"})),
                format_func=lambda x: x['name']
            )
            message = st.text_area("Message")
            
            if st.form_submit_button("Send Notification"):
                for recipient in recipients:
                    notification_data = {
                        'user_id': str(recipient['_id']),
                        'message': message,
                        'type': 'admin_message'
                    }
                    if db_manager.create_notification(notification_data):
                        st.success("Notifications sent!")
                    else:
                        st.error("Failed to send some notifications")
    
    # View all notifications using db_manager
    notifications = pd.DataFrame(list(db.notifications.find()))
    if not notifications.empty:
        st.dataframe(
            notifications[['user_id', 'message', 'type', 'created_at', 'read']],
            hide_index=True
        ) 