import json
from datetime import datetime, timedelta
import re

class TaskExtractor:
    def __init__(self, model):
        self.model = model
        self.role_mappings = {
            # Common variations of roles
            'sales': 'Sales Analyst',
            'sales analyst': 'Sales Analyst',
            'sales rep': 'Sales Analyst',
            'sales representative': 'Sales Analyst',
            
            'presentation': 'Presentation Designer',
            'designer': 'Presentation Designer',
            'presentation designer': 'Presentation Designer',
            
            'engineer': 'Software Engineer',
            'developer': 'Software Engineer',
            'software engineer': 'Software Engineer',
            'programmer': 'Software Engineer',
            
            'marketing': 'Marketing Manager',
            'marketing manager': 'Marketing Manager',
            'marketing lead': 'Marketing Manager'
        }
        
        # Date mapping patterns
        self.date_patterns = {
            r'today': 0,
            r'tomorrow': 1,
            r'day after tomorrow': 2,
            r'next week': 7,
            r'next month': 30,
            r'tonight': 0,
            r'this evening': 0,
            r'this week': 7,
            r'this month': 30,
        }
        
        # Day of week patterns
        self.day_patterns = {
            r'monday': 0,
            r'tuesday': 1,
            r'wednesday': 2,
            r'thursday': 3,
            r'friday': 4,
            r'saturday': 5,
            r'sunday': 6
        }
        
    def normalize_role(self, role):
        if not role:
            return None
            
        role_lower = role.lower().strip()
        for key, value in self.role_mappings.items():
            if key in role_lower:
                return value
        return role
        
    def convert_to_date(self, deadline_str):
        if not deadline_str or deadline_str.lower() == 'not specified':
            return 'Not specified'
            
        deadline_lower = deadline_str.lower().strip()
        today = datetime.now()
        
        # Check for relative day patterns
        for pattern, days in self.date_patterns.items():
            if pattern in deadline_lower:
                future_date = today + timedelta(days=days)
                return future_date.strftime('%Y-%m-%d')
                
        # Check for day of week
        for day_name, day_num in self.day_patterns.items():
            if day_name in deadline_lower:
                current_day = today.weekday()
                days_ahead = day_num - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                future_date = today + timedelta(days=days_ahead)
                return future_date.strftime('%Y-%m-%d')
                
        # Check for "in X days/weeks" pattern
        number_patterns = {
            r'in (\d+) day': 1,
            r'in (\d+) days': 1,
            r'in (\d+) week': 7,
            r'in (\d+) weeks': 7,
            r'in (\d+) month': 30,
            r'in (\d+) months': 30
        }
        
        for pattern, multiplier in number_patterns.items():
            match = re.search(pattern, deadline_lower)
            if match:
                number = int(match.group(1))
                future_date = today + timedelta(days=number * multiplier)
                return future_date.strftime('%Y-%m-%d')
        
        return deadline_str
        
    def extract_tasks(self, transcript):
        prompt = """
        Extract ALL tasks and assignments from the following meeting transcript and format them as a JSON array.
        Analyze the entire transcript carefully to identify every distinct task or assignment mentioned.
        
        Each task object must have these exact fields:
        - task: the task description
        - assignee: the person assigned (if not specified, leave empty)
        - role: must be one of: Sales Analyst, Presentation Designer, Software Engineer, Marketing Manager
        - deadline: when it's due (use exact date if specified, or relative terms like 'tomorrow', 'next week', etc.)
        
        For the role field, analyze the context and task to determine the most appropriate role:
        - sales, reports, analytics, revenue -> Sales Analyst
        - presentations, slides, design, visuals -> Presentation Designer
        - code, development, technical, bugs -> Software Engineer
        - marketing, campaigns, social media, promotion -> Marketing Manager
        
        Important:
        - Create a separate task object for EACH distinct task mentioned
        - If multiple tasks are assigned to the same person, create separate entries
        - If a task is assigned to multiple people, create separate entries for each person
        - If a task is assigned based on a name, assign it to that person. If the name and role do not match (e.g., if 'Prince' is in development but a marketing task is assigned), show a warning and assign it to a user with the matching role.
        - For tasks without explicit deadlines, use "Not specified"
        
        Format the response as valid JSON only, with no additional text.
        
        Example format for multiple tasks:
        [
            {
                "task": "Prepare sales report",
                "assignee": "Alex",
                "role": "Sales Analyst",
                "deadline": "tomorrow"
            },
            {
                "task": "Update website design",
                "assignee": "Sarah",
                "role": "Presentation Designer",
                "deadline": "next week"
            }
        ]

        Transcript:
        """
        
        prompt += transcript
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            print("\nGemini API Response:")
            print(response_text)
            
            # Remove any markdown code block markers
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the response to get JSON array
            tasks = json.loads(response_text)
            
            if not isinstance(tasks, list):
                print("API response was not a list of tasks")
                return []
            
            # Normalize roles and convert deadlines to dates
            for task in tasks:
                if 'role' in task:
                    task['role'] = self.normalize_role(task['role'])
                if 'deadline' in task:
                    task['deadline'] = self.convert_to_date(task['deadline'])
                
                # Check if assignee and role match
                if 'assignee' in task and 'role' in task:
                    assigned_role = task['role']
                    assignee_name = task['assignee']
                    # Find the user by name to get their actual role
                    user = self.find_user_by_name(assignee_name)  # Implement this method to find user by name
                    if user and user['role'] != assigned_role:
                        print(f"Warning: Task '{task['task']}' assigned to '{assignee_name}' with role '{assigned_role}' does not match their actual role. Assigning to a user with the matching role instead.")
                        # Assign to a user with the matching role
                        matching_user = self.find_user_by_role(assigned_role)  # Implement this method to find user by role
                        if matching_user:
                            task['assignee'] = matching_user['name']
                            task['assignee_id'] = str(matching_user['_id'])
                        else:
                            print(f"Warning: No user found with role '{assigned_role}' to assign the task.")

            # Filter out tasks with invalid roles
            valid_tasks = [task for task in tasks if task.get('role') in self.role_mappings.values()]
            
            if len(valid_tasks) < len(tasks):
                print(f"\nWarning: Filtered out {len(tasks) - len(valid_tasks)} tasks with invalid roles")
                
            print("\nExtracted Tasks:")
            for task in valid_tasks:
                print(f"- {task['task']}")
                print(f"  Assigned to: {task['assignee']}")
                print(f"  Role: {task['role']}")
                print(f"  Due: {task['deadline']}")
                print()
                
            return valid_tasks
            
        except json.JSONDecodeError as e:
            print(f"Error parsing tasks from API response: {str(e)}")
            print(f"Raw response: {response_text}")
            return []
        except Exception as e:
            print(f"Error extracting tasks: {str(e)}")
            return [] 

    def find_user_by_name(self, name):
        """Find a user by their name in the database."""
        # Implement logic to query the database for a user by name
        # Return user object or None if not found
        pass

    def find_user_by_role(self, role):
        """Find a user by their role in the database."""
        # Implement logic to query the database for a user by role
        # Return user object or None if not found
        pass 