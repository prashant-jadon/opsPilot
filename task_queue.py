import queue
import threading
from datetime import datetime
import time

class TaskQueue:
    def __init__(self, db_manager):
        self.task_queue = queue.Queue()
        self.db_manager = db_manager
        self.is_running = True
        
        # Start the processing thread
        self.process_thread = threading.Thread(target=self._process_queue)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def add_task(self, task_data):
        """Add a task to the queue"""
        self.task_queue.put(task_data)
        
    def stop(self):
        """Stop the processing thread"""
        self.is_running = False
        self.process_thread.join()
        
    def _process_queue(self):
        """Process tasks from the queue"""
        while self.is_running:
            try:
                # Get task from queue with timeout
                task_data = self.task_queue.get(timeout=1)
                
                try:
                    # Store in MongoDB
                    task_id = self.db_manager.create_task(task_data)  # This returns ObjectId directly
                    if task_id:
                        print(f"\nTask processed and stored:")
                        print(f"Task ID: {task_id}")
                        print(f"Description: {task_data['task_description']}")
                        print(f"Assigned to: {task_data['assignee_name']}")
                        
                        # Create notification
                        notification_data = {
                            'user_id': task_data['assignee_id'],
                            'task_id': str(task_id),
                            'message': f"New task assigned: {task_data['task_description']}",
                            'type': 'new_task'
                        }
                        self.db_manager.create_notification(notification_data)
                    else:
                        print("Failed to store task in database")
                    
                except Exception as e:
                    print(f"Error processing task: {str(e)}")
                    
                finally:
                    # Mark task as done
                    self.task_queue.task_done()
                    
            except queue.Empty:
                # Queue is empty, continue waiting
                continue 