# migrate_data.py
import json
import os
from models import JSONDatabase

def migrate_all_users():
    db = JSONDatabase()
    
    # Migrate all existing user files
    for filename in os.listdir(db.data_dir):
        if filename.startswith('user_') and filename.endswith('.json'):
            user_id = filename.replace('user_', '').replace('.json', '')
            user_file = os.path.join(db.data_dir, filename)
            
            with open(user_file, 'r') as f:
                data = json.load(f)
            
            # Check if migration is needed
            if 'profile' not in data:
                print(f"Migrating user {user_id}...")
                
                # Create new structure
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
                
                # Save migrated data
                with open(user_file, 'w') as f:
                    json.dump(migrated_data, f, indent=2)
                
                print(f"User {user_id} migrated successfully!")
            else:
                print(f"User {user_id} already has the new structure.")

if __name__ == '__main__':
    migrate_all_users()
    print("Migration completed!")