from flask_login import UserMixin
from bson import ObjectId
import bcrypt

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.currency = user_data.get('currency', 'Tsh')
        self.notification_settings = user_data.get('notification_settings', {
            'email': True,
            'bills': True,
            'events': True,
            'time': '09:00'
        })
    
    @staticmethod
    def create_user(db, username, email, password):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'currency': 'Tsh',
            'notification_settings': {
                'email': True,
                'bills': True,
                'events': True,
                'time': '09:00'
            }
        }
        result = db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def verify_password(db, username, password):
        user_data = db.users.find_one({'username': username})
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            return User(user_data)
        return None