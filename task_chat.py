import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class TaskChat:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def get_task_context(self, task_id=None, user=None):
        """Get context about tasks"""
        if user['role'] == 'admin':
            tasks = self.db_manager.get_all_tasks()
            context = "You are a task management assistant. Here are all current tasks:\n\n"
        else:
            # Use tasks provided in user context
            tasks = user.get('tasks', [])
            context = f"""You are a task assistant for {user['name']}, a {user['employee_role']}.
Here are their current tasks:\n\n"""
            
        # Add all tasks to context
        for task in tasks:
            context += f"Task: {task['task_description']}\n"
            context += f"Status: {task['status']}\n"
            context += f"Deadline: {task['deadline']}\n"
            context += f"Priority: {task.get('priority', 'Not set')}\n\n"
            
        context += """
Please help with any questions about these tasks. You can:
- Provide status updates
- Suggest next steps
- Help with prioritization
- Explain task requirements
- Offer guidance and best practices
"""
        return context

    def chat(self, message, task_id=None, user=None):
        """Process chat message and return response"""
        try:
            # Initialize chat history if needed
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Get task context
            context = self.get_task_context(task_id, user)
            
            # Build conversation history
            history = "\n\n".join([
                f"User: {msg['user']}\nAssistant: {msg['assistant']}"
                for msg in st.session_state.chat_history[-5:]  # Last 5 messages for context
            ])
            
            # Construct prompt
            prompt = f"""{context}

Previous conversation:
{history}

User: {message}

Provide a helpful response while considering the task context. Be concise but informative.
"""
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Save to chat history
            st.session_state.chat_history.append({
                'user': message,
                'assistant': response.text,
                'timestamp': datetime.now(),
                'task_id': task_id
            })
            
            return response.text
            
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return "I'm sorry, I encountered an error. Please try again."

def show_chat_interface(task_chat, task_id=None, user=None):
    """Display chat interface in Streamlit"""
    st.markdown("### 💬 Task Chat Assistant")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat input
    message = st.chat_input("Ask a question about your task...")
    
    if message:
        response = task_chat.chat(message, task_id, user)
        
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(msg['user'])
        with st.chat_message("assistant"):
            st.write(msg['assistant']) 