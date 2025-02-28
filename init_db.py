from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from auth import hash_password

load_dotenv()

def init_database():
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client.task_manager
    
    # Create indexes
    db.users.create_index("email", unique=True)
    db.tasks.create_index("assignee_id")
    db.notifications.create_index("user_id")
    
    # Create default admin if not exists
    if not db.users.find_one({"email": "admin@example.com"}):
        admin_user = {
            "name": "Admin",
            "email": "admin@example.com",
            "password": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.now()
        }
        db.users.insert_one(admin_user)
        print("Created default admin user")
    
    print("Database initialized successfully")

if __name__ == "__main__":
    init_database() 