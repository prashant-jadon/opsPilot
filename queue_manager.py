import queue
import threading
from datetime import datetime
import time
import os
import json
from pathlib import Path

class QueueManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueueManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.task_queue = queue.Queue()
        self.is_running = True
        self.status_file = Path('queue_status.json')
        self._update_status()
    
    def add_task(self, task_data):
        """Add a task to the queue"""
        self.task_queue.put(task_data)
        self._update_status()
        
    def get_status(self):
        """Get current queue status"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
            
        return {
            'queued_tasks': 0,
            'processing': False
        }
    
    def _update_status(self):
        """Update queue status file"""
        status = {
            'queued_tasks': self.task_queue.qsize(),
            'processing': not self.task_queue.empty()
        }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f)
        except Exception as e:
            print(f"Error updating queue status: {str(e)}")

class TaskQueue:
    def __init__(self, db_manager):
        self.queue_manager = QueueManager()
        self.db_manager = db_manager
        
        # Start the processing thread
        self.process_thread = threading.Thread(target=self._process_queue)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def add_task(self, task_data):
        """Add a task to the queue"""
        self.queue_manager.add_task(task_data)
        
    def stop(self):
        """Stop the processing thread"""
        self.queue_manager.is_running = False
        self.process_thread.join()
        
    def _process_queue(self):
        """Process tasks from the queue"""
        while self.queue_manager.is_running:
            try:
                # Get task from queue with timeout
                task_data = self.queue_manager.task_queue.get(timeout=1)
                
                try:
                    # Store in MongoDB
                    result = self.db_manager.create_task(task_data)
                    print(f"\nTask processed and stored:")
                    print(f"Task ID: {result.inserted_id}")
                    print(f"Description: {task_data['task_description']}")
                    print(f"Assigned to: {task_data['assignee_name']}")
                    
                except Exception as e:
                    print(f"Error processing task: {str(e)}")
                    
                finally:
                    # Mark task as done
                    self.queue_manager.task_queue.task_done()
                    self.queue_manager._update_status()
                    
            except queue.Empty:
                # Queue is empty, continue waiting
                continue 