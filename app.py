# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Data storage
DATA_FILE = 'data.json'

class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

# Mock user database
users = {
    '1': User('1', 'admin', 'admin@example.com', generate_password_hash('password'))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'users': {},
        'events': {},
        'expenses': {},
        'incomes': {},
        'budgets': {},
        'goals': {},
        'tasks': {},
        'bills': {}
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = next((u for u in users.values() if u.username == username), None)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Please fill all fields')
        else:
            user_id = str(len(users) + 1)
            users[user_id] = User(user_id, username, email, generate_password_hash(password))
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
    return render_template('register.html')

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

# API Endpoints
@app.route('/api/add_expense', methods=['POST'])
@login_required
def add_expense():
    try:
        data = request.json
        if not all(k in data for k in ['amount', 'category', 'date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        expense_id = str(len(db['expenses']) + 1)
        db['expenses'][expense_id] = {
            'amount': float(data['amount']),
            'category': data['category'],
            'date': data['date'],
            'description': data.get('description', ''),
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': expense_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/add_income', methods=['POST'])
@login_required
def add_income():
    try:
        data = request.json
        if not all(k in data for k in ['amount', 'source', 'date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        income_id = str(len(db['incomes']) + 1)
        db['incomes'][income_id] = {
            'amount': float(data['amount']),
            'source': data['source'],
            'date': data['date'],
            'description': data.get('description', ''),
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': income_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/add_event', methods=['POST'])
@login_required
def add_event():
    try:
        data = request.json
        if not all(k in data for k in ['title', 'start', 'end']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        event_id = str(len(db['events']) + 1)
        db['events'][event_id] = {
            'title': data['title'],
            'start': data['start'],
            'end': data['end'],
            'description': data.get('description', ''),
            'recurring': data.get('recurring', False),
            'recurrence_pattern': data.get('recurrence_pattern', None),
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': event_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/add_task', methods=['POST'])
@login_required
def add_task():
    try:
        data = request.json
        if not all(k in data for k in ['name', 'due_date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        task_id = str(len(db['tasks']) + 1)
        db['tasks'][task_id] = {
            'name': data['name'],
            'due_date': data['due_date'],
            'priority': data.get('priority', 'medium'),
            'description': data.get('description', ''),
            'completed': False,
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': task_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/add_bill', methods=['POST'])
@login_required
def add_bill():
    try:
        data = request.json
        if not all(k in data for k in ['name', 'amount', 'due_date']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        bill_id = str(len(db['bills']) + 1)
        db['bills'][bill_id] = {
            'name': data['name'],
            'amount': float(data['amount']),
            'due_date': data['due_date'],
            'recurring': data.get('recurring', 'none'),
            'paid': False,
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': bill_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/add_budget', methods=['POST'])
@login_required
def add_budget():
    try:
        data = request.json
        if not all(k in data for k in ['category', 'amount', 'month']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        budget_id = f"{data['month']}_{data['category']}"
        db['budgets'][budget_id] = {
            'category': data['category'],
            'amount': float(data['amount']),
            'month': data['month'],
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': budget_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/add_goal', methods=['POST'])
@login_required
def add_goal():
    try:
        data = request.json
        if not all(k in data for k in ['name', 'amount']):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        db = load_data()
        goal_id = str(len(db['goals']) + 1)
        db['goals'][goal_id] = {
            'name': data['name'],
            'target_amount': float(data['amount']),
            'current_amount': float(data.get('current_amount', 0)),
            'target_date': data.get('target_date', None),
            'user_id': current_user.id
        }
        save_data(db)
        return jsonify({'status': 'success', 'id': goal_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Data retrieval endpoints
@app.route('/api/get_expenses')
@login_required
def get_expenses():
    db = load_data()
    user_expenses = {k: v for k, v in db.get('expenses', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_expenses)

@app.route('/api/get_incomes')
@login_required
def get_incomes():
    db = load_data()
    user_incomes = {k: v for k, v in db.get('incomes', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_incomes)

@app.route('/api/get_events')
@login_required
def get_events():
    db = load_data()
    user_events = {k: v for k, v in db.get('events', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_events)

@app.route('/api/get_tasks')
@login_required
def get_tasks():
    db = load_data()
    user_tasks = {k: v for k, v in db.get('tasks', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_tasks)

@app.route('/api/get_bills')
@login_required
def get_bills():
    db = load_data()
    user_bills = {k: v for k, v in db.get('bills', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_bills)

@app.route('/api/get_budgets')
@login_required
def get_budgets():
    db = load_data()
    user_budgets = {k: v for k, v in db.get('budgets', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_budgets)

@app.route('/api/get_goals')
@login_required
def get_goals():
    db = load_data()
    user_goals = {k: v for k, v in db.get('goals', {}).items() if v.get('user_id') == current_user.id}
    return jsonify(user_goals)

@app.route('/api/get_financial_summary')
@login_required
def get_financial_summary():
    db = load_data()
    
    user_expenses = [float(e['amount']) for e in db.get('expenses', {}).values() if e.get('user_id') == current_user.id]
    user_incomes = [float(i['amount']) for i in db.get('incomes', {}).values() if i.get('user_id') == current_user.id]
    
    total_income = sum(user_incomes)
    total_expense = sum(user_expenses)
    balance = total_income - total_expense
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    })

@app.route('/api/delete_item/<item_type>/<item_id>', methods=['DELETE'])
@login_required
def delete_item(item_type, item_id):
    try:
        valid_types = ['expenses', 'incomes', 'events', 'tasks', 'bills', 'budgets', 'goals']
        if item_type not in valid_types:
            return jsonify({'status': 'error', 'message': 'Invalid item type'}), 400
        
        db = load_data()
        if item_id in db.get(item_type, {}):
            # Verify the item belongs to the current user
            if db[item_type][item_id].get('user_id') == current_user.id:
                del db[item_type][item_id]
                save_data(db)
                return jsonify({'status': 'success'})
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        return jsonify({'status': 'error', 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)