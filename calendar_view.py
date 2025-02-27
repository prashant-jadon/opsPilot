import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import calendar
from config import ThemeConfig as theme

class CalendarView:
    def __init__(self):
        self.today = datetime.now()
        self.colors = {
            'pending': theme.BG_WARNING,
            'in_progress': theme.BG_PRIMARY,
            'completed': theme.BG_SUCCESS,
            'overdue': theme.BG_DANGER,
            'weekend': "#F9FAFB",
            'today': theme.BG_SECONDARY
        }
        self.text_color = theme.TEXT_PRIMARY
        # Add border colors for markers
        self.border_colors = {
            'pending': theme.WARNING,
            'in_progress': theme.PRIMARY,
            'completed': theme.SUCCESS,
            'overdue': theme.DANGER
        }

    def create_calendar(self, tasks, year=None, month=None):
        """Create an interactive calendar with tasks"""
        if year is None:
            year = self.today.year
        if month is None:
            month = self.today.month

        # Get calendar data for the month
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Process tasks
        task_dates = {}
        for task in tasks:
            deadline = pd.to_datetime(task['deadline']) if task['deadline'] != 'Not specified' else None
            if deadline:
                date_str = deadline.strftime('%Y-%m-%d')
                if date_str not in task_dates:
                    task_dates[date_str] = []
                task_dates[date_str].append({
                    'description': task['task_description'],
                    'status': task['status'],
                    'assignee': task.get('assignee_name', 'Unassigned')
                })

        # Create calendar grid
        fig = go.Figure()

        # Add cells for each day
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day != 0:
                    date = datetime(year, month, day)
                    date_str = date.strftime('%Y-%m-%d')
                    
                    # Determine cell color
                    if date.strftime('%Y-%m-%d') == self.today.strftime('%Y-%m-%d'):
                        color = self.colors['today']
                    elif date.weekday() >= 5:  # Weekend
                        color = self.colors['weekend']
                    else:
                        color = 'white'
                    
                    # Create cell with black text
                    fig.add_trace(go.Scatter(
                        x=[day_num + 0.5],
                        y=[6 - week_num - 0.5],
                        mode='text',
                        text=str(day),
                        textfont=dict(
                            color=self.text_color,
                            size=14
                        ),
                        hoverinfo='text',
                        showlegend=False
                    ))
                    
                    # Add task indicators with improved visibility
                    if date_str in task_dates:
                        for i, task in enumerate(task_dates[date_str]):
                            # Add larger, more visible markers
                            fig.add_trace(go.Scatter(
                                x=[day_num + 0.5],  # Centered in the cell
                                y=[6 - week_num - 0.75],  # Slightly lower
                                mode='markers',
                                marker=dict(
                                    size=16,  # Increased size
                                    symbol='circle',
                                    color=self.colors[task['status']],
                                    line=dict(
                                        color=self.border_colors[task['status']],
                                        width=2  # Thicker border
                                    )
                                ),
                                hovertext=(
                                    f"<b>{task['description']}</b><br>"
                                    f"Status: {task['status'].replace('_', ' ').title()}<br>"
                                    f"Assignee: {task['assignee']}"
                                ),
                                hoverinfo='text',
                                showlegend=False
                            ))
                            
                            # Add a small label below the marker
                            fig.add_trace(go.Scatter(
                                x=[day_num + 0.5],
                                y=[6 - week_num - 0.9],
                                mode='text',
                                text='📅',  # Calendar emoji as indicator
                                textfont=dict(
                                    size=10,
                                    color=self.border_colors[task['status']]
                                ),
                                hoverinfo='skip',
                                showlegend=False
                            ))

        # Configure layout with improved text visibility
        fig.update_layout(
            title=dict(
                text=f"{month_name} {year}",
                font=dict(color=self.text_color, size=20)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            height=500,
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E7EB',
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                tickvals=list(range(7)),
                range=[-0.5, 6.5],
                tickfont=dict(color=self.text_color)
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E5E7EB',
                ticktext=['Week 6', 'Week 5', 'Week 4', 'Week 3', 'Week 2', 'Week 1'],
                tickvals=list(range(6)),
                range=[-0.5, 5.5],
                tickfont=dict(color=self.text_color)
            )
        )

        # Add legend with improved visibility
        for status, color in [
            ('Pending', self.colors['pending']),
            ('In Progress', self.colors['in_progress']),
            ('Completed', self.colors['completed'])
        ]:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(
                    size=16,  # Match the size of calendar markers
                    color=color,
                    line=dict(
                        color=self.border_colors[status.lower().replace(' ', '_')],
                        width=2
                    )
                ),
                name=status
            ))

        return fig

def show_calendar(tasks, user_role="employee"):
    """Display the calendar in the Streamlit app"""
    st.markdown("### 📅 Task Calendar")
    
    # Calendar navigation
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        if st.button("◀ Previous Month"):
            if 'calendar_month' not in st.session_state:
                st.session_state.calendar_month = datetime.now().month
                st.session_state.calendar_year = datetime.now().year
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
                
    with col2:
        st.markdown(
            f"<h3 style='text-align: center;'>{calendar.month_name[st.session_state.get('calendar_month', datetime.now().month)]} "
            f"{st.session_state.get('calendar_year', datetime.now().year)}</h3>",
            unsafe_allow_html=True
        )
        
    with col3:
        if st.button("Next Month ▶"):
            if 'calendar_month' not in st.session_state:
                st.session_state.calendar_month = datetime.now().month
                st.session_state.calendar_year = datetime.now().year
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1

    # Initialize calendar view and display
    calendar_view = CalendarView()
    fig = calendar_view.create_calendar(
        tasks,
        st.session_state.get('calendar_year', datetime.now().year),
        st.session_state.get('calendar_month', datetime.now().month)
    )
    st.plotly_chart(fig, use_container_width=True) 