import speech_recognition as sr
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
import json
import os
from task_extractor import TaskExtractor
from database_manager import DatabaseManager
from audio_processor import AudioProcessor
from config import load_config
from task_queue import TaskQueue
from dotenv import load_dotenv

class MeetingTaskManager:
    def __init__(self):
        # Load configuration
        config = load_config()
        load_dotenv()
        
        # Initialize MongoDB connection
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client.task_manager
        
        # Initialize Gemini API
        genai.configure(api_key=config['gemini_api_key'])
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize components
        self.db_manager = DatabaseManager(self.db)
        self.task_extractor = TaskExtractor(self.model)
        self.audio_processor = AudioProcessor()
        
        # Initialize task queue
        self.task_queue = TaskQueue(self.db_manager)
    
    def start_meeting(self):
        print("Starting meeting recording...")
        print("Press Ctrl+C to stop the meeting")
        try:
            while True:
                try:
                    # Get audio transcript
                    transcript = self.audio_processor.capture_audio()
                    if not transcript:
                        continue
                    
                    print("\nTranscript:", transcript)
                        
                    # Extract tasks using Gemini
                    tasks = self.task_extractor.extract_tasks(transcript)
                    
                    # Process and queue tasks
                    for task in tasks:
                        # Find employee by role
                        employee = self.db_manager.get_user_by_role(task['role'])
                        if employee:
                            task_data = {
                                'task_description': task['task'],
                                'assignee_name': employee['name'],
                                'assignee_id': str(employee['_id']),
                                'role': task['role'],
                                'deadline': task['deadline'],
                                'status': 'pending',
                                'created_at': datetime.now(),
                                'original_transcript': transcript
                            }
                            
                            # Add task to queue for processing
                            self.task_queue.add_task(task_data)
                            print(f"\nTask queued: {task_data['task_description']}")
                        else:
                            print(f"\nWarning: No employee found for role: {task['role']}")
                        
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:
                    print(f"Error occurred: {str(e)}")
                    
        except KeyboardInterrupt:
            print("\nMeeting recording stopped.")
        finally:
            # Clean up
            self.task_queue.stop()
            self.client.close()

    def process_task(self, task, db_manager):
        employee = db_manager.get_user_by_role(task['role'])
        if employee:
            task_data = {
                'task_description': task['task'],
                'assignee_id': str(employee['_id']),
                'assignee_name': employee['name'],
                'role': task['role'],
                'deadline': task['deadline'],
                'status': 'pending',
                'created_at': datetime.now()
            }
            
            task_id = db_manager.create_task(task_data)
            if task_id:
                # Create notification
                notification_data = {
                    'user_id': task_data['assignee_id'],
                    'task_id': str(task_id),
                    'message': f"New task assigned: {task_data['task_description']}",
                    'type': 'new_task'
                }
                db_manager.create_notification(notification_data)
                return True
        return False

if __name__ == "__main__":
    manager = MeetingTaskManager()
    manager.start_meeting() 