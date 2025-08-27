from flask import Flask, render_template
from flask_login import LoginManager, current_user
import os
from dotenv import load_dotenv
from datetime import datetime


# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key'  

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login' 

# Import database after app initialization to avoid circular imports
from database import db

# Import user model after app initialization to avoid circular imports
from models import User

@login_manager.user_loader
def load_user(user_id):
    from bson import ObjectId
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Now import blueprints AFTER creating the app and login_manager
from auth import auth_bp
from routes.money import money_bp
from routes.events import events_bp
from routes.reports import reports_bp
from routes.settings import settings_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(money_bp)
app.register_blueprint(events_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(settings_bp)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# Context processor to make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
    