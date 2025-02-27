from pymongo import MongoClient
import os
from datetime import datetime
from bson import ObjectId

class DatabaseManager:
    def __init__(self, db):
        self.db = db
        
    def create_user(self, user_data):
        try:
            result = self.db.users.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return None
            
    def get_user(self, email):
        return self.db.users.find_one({"email": email})
        
    def get_user_by_id(self, user_id):
        return self.db.users.find_one({"_id": ObjectId(user_id)})
        
    def update_user(self, user_id, update_data):
        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return False
            
    def delete_user(self, user_id):
        try:
            result = self.db.users.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return False
            
    def create_task(self, task_data):
        try:
            # Ensure task has required fields
            required_fields = ['task_description', 'assignee_id', 'assignee_name', 
                             'role', 'deadline', 'status']
            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"Missing required field: {field}")
                    
            task_data['created_at'] = datetime.now()
            result = self.db.tasks.insert_one(task_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating task: {str(e)}")
            return None
            
    def update_task(self, task_id, update_data):
        try:
            update_data['updated_at'] = datetime.now()
            result = self.db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            return False
            
    def get_user_tasks(self, user_id):
        try:
            return list(self.db.tasks.find({"assignee_id": user_id}))
        except Exception as e:
            print(f"Error getting user tasks: {str(e)}")
            return []
            
    def create_notification(self, notification_data):
        try:
            notification_data['created_at'] = datetime.now()
            notification_data['read'] = False
            result = self.db.notifications.insert_one(notification_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating notification: {str(e)}")
            return None
            
    def mark_notification_read(self, notification_id):
        try:
            result = self.db.notifications.update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {"read": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error marking notification as read: {str(e)}")
            return False
            
    def get_unread_notifications(self, user_id):
        try:
            return list(self.db.notifications.find({
                "user_id": user_id,
                "read": False
            }))
        except Exception as e:
            print(f"Error getting notifications: {str(e)}")
            return []
        
    def find_employee_by_role(self, role):
        return self.db.employees.find_one({'role': role})
        
    def get_all_pending_tasks(self):
        return list(self.db.tasks.find(
            {'status': 'pending'},
            sort=[('created_at', -1)]
        ))
        
    def update_task_status(self, task_id, status):
        return self.db.tasks.update_one(
            {'_id': task_id},
            {'$set': {
                'status': status,
                'updated_at': datetime.now()
            }}
        )
        
    def get_user_by_role(self, role):
        """Find a user by their employee role"""
        try:
            return self.db.users.find_one({
                "role": "employee",
                "employee_role": role
            })
        except Exception as e:
            print(f"Error finding user by role: {str(e)}")
            return None

    def get_all_tasks(self):
        """Get all tasks from the database"""
        try:
            tasks = list(self.db.tasks.find())
            return tasks
        except Exception as e:
            print(f"Error getting all tasks: {str(e)}")
            return []

    def get_task(self, task_id):
        """Get a specific task by ID"""
        try:
            task = self.db.tasks.find_one({"_id": ObjectId(task_id)})
            return task
        except Exception as e:
            print(f"Error getting task {task_id}: {str(e)}")
            return None

    def get_user_by_name(self, name):
        """Get user by their name"""
        try:
            user = self.db.users.find_one({"name": name})
            return user
        except Exception as e:
            print(f"Error getting user by name {name}: {str(e)}")
            return None

    def get_users_by_role(self, role):
        """Get all users with a specific role"""
        try:
            users = list(self.db.users.find({"employee_role": role}))
            return users
        except Exception as e:
            print(f"Error getting users by role {role}: {str(e)}")
            return [] 