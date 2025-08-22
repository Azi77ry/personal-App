# models.py
import json
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class JSONDatabase:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def get_user_file(self, user_id):
        return os.path.join(self.data_dir, f'user_{user_id}.json')
    
    def load_user_data(self, user_id):
        user_file = self.get_user_file(user_id)
        if os.path.exists(user_file):
            with open(user_file, 'r') as f:
                data = json.load(f)
                # Migrate old data structure to new one if needed
                return self.migrate_data_structure(data)
        return self.get_default_user_data()
    
    def migrate_data_structure(self, data):
        """Migrate from old data structure to new one"""
        # Check if this is the old structure (without profile)
        if 'profile' not in data:
            # Create new structure with profile
            migrated_data = {
                'profile': {
                    'username': data.get('username', ''),
                    'email': data.get('email', ''),
                    'email_verified': data.get('email_verified', False)
                },
                'settings': data.get('settings', {
                    'currency': 'USD',
                    'notifications': {
                        'email': True,
                        'bills': True,
                        'events': True,
                        'time': '09:00'
                    }
                }),
                'expenses': data.get('expenses', {}),
                'incomes': data.get('incomes', {}),
                'events': data.get('events', {}),
                'budgets': data.get('budgets', {}),
                'goals': data.get('goals', {}),
                'tasks': data.get('tasks', {}),
                'bills': data.get('bills', {})
            }
            return migrated_data
        return data
    
    def get_default_user_data(self):
        return {
            'expenses': {},
            'incomes': {},
            'events': {},
            'budgets': {},
            'goals': {},
            'tasks': {},
            'bills': {},
            'settings': {
                'currency': 'USD',
                'notifications': {
                    'email': True,
                    'bills': True,
                    'events': True,
                    'time': '09:00'
                }
            },
            'profile': {
                'username': '',
                'email': '',
                'email_verified': False
            }
        }
    
    def save_user_data(self, user_id, data):
        user_file = self.get_user_file(user_id)
        with open(user_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def user_exists(self, username, email=None):
        # Check all user files for this username or email
        for filename in os.listdir(self.data_dir):
            if filename.startswith('user_') and filename.endswith('.json'):
                with open(os.path.join(self.data_dir, filename), 'r') as f:
                    user_data = json.load(f)
                    # Handle both old and new data structures
                    if 'profile' in user_data:
                        # New structure
                        profile = user_data['profile']
                        if profile.get('username') == username:
                            return True
                        if email and profile.get('email') == email:
                            return True
                    else:
                        # Old structure
                        if user_data.get('username') == username:
                            return True
                        if email and user_data.get('email') == email:
                            return True
        return False
    
    def get_user_by_username(self, username):
        for filename in os.listdir(self.data_dir):
            if filename.startswith('user_') and filename.endswith('.json'):
                with open(os.path.join(self.data_dir, filename), 'r') as f:
                    user_data = json.load(f)
                    # Handle both old and new data structures
                    if 'profile' in user_data:
                        # New structure
                        if user_data['profile'].get('username') == username:
                            user_id = filename.replace('user_', '').replace('.json', '')
                            return user_id, user_data
                    else:
                        # Old structure
                        if user_data.get('username') == username:
                            user_id = filename.replace('user_', '').replace('.json', '')
                            return user_id, user_data
        return None, None
    
    def get_user_by_email(self, email):
        for filename in os.listdir(self.data_dir):
            if filename.startswith('user_') and filename.endswith('.json'):
                with open(os.path.join(self.data_dir, filename), 'r') as f:
                    user_data = json.load(f)
                    # Handle both old and new data structures
                    if 'profile' in user_data:
                        # New structure
                        if user_data['profile'].get('email') == email:
                            user_id = filename.replace('user_', '').replace('.json', '')
                            return user_id, user_data
                    else:
                        # Old structure
                        if user_data.get('email') == email:
                            user_id = filename.replace('user_', '').replace('.json', '')
                            return user_id, user_data
        return None, None

# Initialize database
db = JSONDatabase()