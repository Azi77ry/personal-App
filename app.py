# app.py - Complete version with all API endpoints (email verification removed)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import json
import os
import re
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-super-secret-key-here')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# app.py - Update the User class
class User(UserMixin):
    def __init__(self, id, username, email, password_hash, email_verified=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.email_verified = email_verified
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def load_users():
    users = {}
    if not os.path.exists('users.json'):
        return users
    
    with open('users.json', 'r') as f:
        try:
            users_data = json.load(f)
            for user_id, user_data in users_data.items():
                users[user_id] = User(
                    user_id, 
                    user_data['username'], 
                    user_data['email'], 
                    user_data['password_hash'],
                    user_data.get('email_verified', False)
                )
        except:
            pass
    return users

def save_users(users):
    users_data = {}
    for user_id, user in users.items():
        users_data[user_id] = {
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash
        }
    
    with open('users.json', 'w') as f:
        json.dump(users_data, f, indent=2)

# Load users at startup
users = load_users()

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Validation functions
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    return True, ""

def validate_amount(amount):
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be greater than zero"
        return True, ""
    except ValueError:
        return False, "Amount must be a valid number"

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = next((u for u in users.values() if u.username == username), None)
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Please fill all fields', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif not validate_email(email):
            flash('Please enter a valid email address', 'danger')
        elif db.user_exists(username, email):
            flash('Username or email already exists', 'danger')
        else:
            # Validate password strength
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, 'danger')
                return render_template('register.html')
            
            # Create new user
            user_id = str(uuid.uuid4())  # Use UUID instead of sequential ID
            users[user_id] = User(
                user_id, 
                username, 
                email, 
                generate_password_hash(password),
                False
            )
            save_users(users)
            
            # Create user data file with new structure
            user_data = db.get_default_user_data()
            user_data['profile'] = {
                'username': username,
                'email': email,
                'email_verified': False
            }
            db.save_user_data(user_id, user_data)
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Add this helper method to the app
def get_default_user_data():
    return {
        'expenses': {},
        'incomes': {},
        'events': {},
        'budgets': {},
        'goals': {},
        'tasks': {},
        'bills': {},
        'settings': { 
            'currency': 'Tsh',
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

# Main application routes
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/money')
@login_required
def money():
    return render_template('money.html')

@app.route('/events')
@login_required
def events():
    return render_template('events.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# API Endpoints with complete functionality

# Expenses API
@app.route('/api/add_expense', methods=['POST'])
@login_required
def add_expense():
    try:
        data = request.json
        if not all(k in data for k in ['amount', 'category', 'date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Validate amount
        is_valid, message = validate_amount(data['amount'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        user_data = db.load_user_data(current_user.id)
        expense_id = str(uuid.uuid4())
        user_data['expenses'][expense_id] = {
            'amount': float(data['amount']),
            'category': data['category'],
            'date': data['date'],
            'description': data.get('description', ''),
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': expense_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Incomes API
@app.route('/api/add_income', methods=['POST'])
@login_required
def add_income():
    try:
        data = request.json
        if not all(k in data for k in ['amount', 'source', 'date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Validate amount
        is_valid, message = validate_amount(data['amount'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        user_data = db.load_user_data(current_user.id)
        income_id = str(uuid.uuid4())
        user_data['incomes'][income_id] = {
            'amount': float(data['amount']),
            'source': data['source'],
            'date': data['date'],
            'description': data.get('description', ''),
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': income_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Events API
@app.route('/api/add_event', methods=['POST'])
@login_required
def add_event():
    try:
        data = request.json
        if not all(k in data for k in ['title', 'start', 'end']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Validate dates
        try:
            start_date = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
            if start_date >= end_date:
                return jsonify({'status': 'error', 'message': 'End date must be after start date'}), 400
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400
        
        user_data = db.load_user_data(current_user.id)
        event_id = str(uuid.uuid4())
        user_data['events'][event_id] = {
            'title': data['title'],
            'start': data['start'],
            'end': data['end'],
            'description': data.get('description', ''),
            'recurring': data.get('recurring', False),
            'recurrence_pattern': data.get('recurrence_pattern', None),
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': event_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Tasks API
@app.route('/api/add_task', methods=['POST'])
@login_required
def add_task():
    try:
        data = request.json
        if not all(k in data for k in ['name', 'due_date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        user_data = db.load_user_data(current_user.id)
        task_id = str(uuid.uuid4())
        user_data['tasks'][task_id] = {
            'name': data['name'],
            'due_date': data['due_date'],
            'priority': data.get('priority', 'medium'),
            'description': data.get('description', ''),
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': task_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Bills API
@app.route('/api/add_bill', methods=['POST'])
@login_required
def add_bill():
    try:
        data = request.json
        if not all(k in data for k in ['name', 'amount', 'due_date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Validate amount
        is_valid, message = validate_amount(data['amount'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        user_data = db.load_user_data(current_user.id)
        bill_id = str(uuid.uuid4())
        user_data['bills'][bill_id] = {
            'name': data['name'],
            'amount': float(data['amount']),
            'due_date': data['due_date'],
            'recurring': data.get('recurring', 'none'),
            'paid': False,
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': bill_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Budgets API
@app.route('/api/add_budget', methods=['POST'])
@login_required
def add_budget():
    try:
        data = request.json
        if not all(k in data for k in ['category', 'amount', 'month']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Validate amount
        is_valid, message = validate_amount(data['amount'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        user_data = db.load_user_data(current_user.id)
        budget_id = f"{data['month']}_{data['category']}"
        user_data['budgets'][budget_id] = {
            'category': data['category'],
            'amount': float(data['amount']),
            'month': data['month'],
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': budget_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Goals API
@app.route('/api/add_goal', methods=['POST'])
@login_required
def add_goal():
    try:
        data = request.json
        if not all(k in data for k in ['name', 'target_amount']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Validate amount
        is_valid, message = validate_amount(data['target_amount'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        user_data = db.load_user_data(current_user.id)
        goal_id = str(uuid.uuid4())
        user_data['goals'][goal_id] = {
            'name': data['name'],
            'target_amount': float(data['target_amount']),
            'current_amount': float(data.get('current_amount', 0)),
            'target_date': data.get('target_date', None),
            'created_at': datetime.now().isoformat()
        }
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success', 'id': goal_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Update goal progress
@app.route('/api/update_goal_progress/<goal_id>', methods=['PUT'])
@login_required
def update_goal_progress(goal_id):
    try:
        data = request.json
        if 'current_amount' not in data:
            return jsonify({'status': 'error', 'message': 'Missing current_amount'}), 400
        
        # Validate amount
        is_valid, message = validate_amount(data['current_amount'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        user_data = db.load_user_data(current_user.id)
        if goal_id not in user_data['goals']:
            return jsonify({'status': 'error', 'message': 'Goal not found'}), 404
        
        user_data['goals'][goal_id]['current_amount'] = float(data['current_amount'])
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Mark bill as paid
@app.route('/api/mark_bill_paid/<bill_id>', methods=['PUT'])
@login_required
def mark_bill_paid(bill_id):
    try:
        user_data = db.load_user_data(current_user.id)
        if bill_id not in user_data['bills']:
            return jsonify({'status': 'error', 'message': 'Bill not found'}), 404
        
        user_data['bills'][bill_id]['paid'] = True
        user_data['bills'][bill_id]['paid_date'] = datetime.now().isoformat()
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Mark task as completed
@app.route('/api/mark_task_completed/<task_id>', methods=['PUT'])
@login_required
def mark_task_completed(task_id):
    try:
        user_data = db.load_user_data(current_user.id)
        if task_id not in user_data['tasks']:
            return jsonify({'status': 'error', 'message': 'Task not found'}), 404
        
        user_data['tasks'][task_id]['completed'] = True
        user_data['tasks'][task_id]['completed_date'] = datetime.now().isoformat()
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Data retrieval endpoints
@app.route('/api/get_expenses')
@login_required
def get_expenses():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('expenses', {}))

@app.route('/api/get_incomes')
@login_required
def get_incomes():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('incomes', {}))

@app.route('/api/get_events')
@login_required
def get_events():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('events', {}))

@app.route('/api/get_tasks')
@login_required
def get_tasks():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('tasks', {}))

@app.route('/api/get_bills')
@login_required
def get_bills():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('bills', {}))

@app.route('/api/get_budgets')
@login_required
def get_budgets():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('budgets', {}))

@app.route('/api/get_goals')
@login_required
def get_goals():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('goals', {}))

@app.route('/api/get_settings')
@login_required
def get_settings():
    user_data = db.load_user_data(current_user.id)
    return jsonify(user_data.get('settings', {}))

@app.route('/api/get_financial_summary')
@login_required
def get_financial_summary():
    user_data = db.load_user_data(current_user.id)
    
    expenses = user_data.get('expenses', {})
    incomes = user_data.get('incomes', {})
    
    total_income = sum(float(income['amount']) for income in incomes.values())
    total_expense = sum(float(expense['amount']) for expense in expenses.values())
    balance = total_income - total_expense
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    })

# Update settings
@app.route('/api/update_settings', methods=['POST'])
@login_required
def update_settings():
    try:
        data = request.json
        user_data = db.load_user_data(current_user.id)
        
        if 'settings' in data:
            user_data['settings'] = {**user_data.get('settings', {}), **data['settings']}
        
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Update profile
@app.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.json
        user_data = db.load_user_data(current_user.id)
        
        if 'username' in data:
            # Check if username is already taken by another user
            if data['username'] != current_user.username and db.user_exists(data['username']):
                return jsonify({'status': 'error', 'message': 'Username already taken'}), 400
            user_data['profile']['username'] = data['username']
            users[current_user.id].username = data['username']
        
        if 'email' in data:
            # Check if email is valid and not already taken
            if not validate_email(data['email']):
                return jsonify({'status': 'error', 'message': 'Invalid email address'}), 400
            if data['email'] != current_user.email and db.user_exists(None, data['email']):
                return jsonify({'status': 'error', 'message': 'Email already taken'}), 400
            user_data['profile']['email'] = data['email']
            users[current_user.id].email = data['email']
        
        db.save_user_data(current_user.id, user_data)
        save_users(users)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Change password
@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.json
        if not all(k in data for k in ['current_password', 'new_password']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Verify current password
        if not current_user.check_password(data['current_password']):
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 400
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Update password
        users[current_user.id].password_hash = generate_password_hash(data['new_password'])
        save_users(users)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Export data
@app.route('/api/export_data')
@login_required
def export_data():
    try:
        user_data = db.load_user_data(current_user.id)
        # Remove sensitive information
        export_data = {k: v for k, v in user_data.items() if k not in ['profile', 'settings']}
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Import data
@app.route('/api/import_data', methods=['POST'])
@login_required
def import_data():
    try:
        data = request.json
        user_data = db.load_user_data(current_user.id)
        
        # Merge imported data with existing data
        for key in ['expenses', 'incomes', 'events', 'tasks', 'bills', 'budgets', 'goals']:
            if key in data:
                user_data[key] = {**user_data.get(key, {}), **data[key]}
        
        db.save_user_data(current_user.id, user_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Reset data
@app.route('/api/reset_data', methods=['POST'])
@login_required
def reset_data():
    try:
        # Keep only profile and settings, reset everything else
        user_data = db.load_user_data(current_user.id)
        profile = user_data.get('profile', {})
        settings = user_data.get('settings', {})
        
        reset_data = {
            'profile': profile,
            'settings': settings,
            'expenses': {},
            'incomes': {},
            'events': {},
            'budgets': {},
            'goals': {},
            'tasks': {},
            'bills': {}
        }
        
        db.save_user_data(current_user.id, reset_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/delete_item/<item_type>/<item_id>', methods=['DELETE'])
@login_required
def delete_item(item_type, item_id):
    try:
        valid_types = ['expenses', 'incomes', 'events', 'tasks', 'bills', 'budgets', 'goals']
        if item_type not in valid_types:
            return jsonify({'status': 'error', 'message': 'Invalid item type'}), 400
        
        user_data = db.load_user_data(current_user.id)
        if item_id in user_data.get(item_type, {}):
            del user_data[item_type][item_id]
            db.save_user_data(current_user.id, user_data)
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(401)
def unauthorized_error(error):
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)