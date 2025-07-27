# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# Data storage (in a real app, use a database)
DATA_FILE = 'data.json'

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
        'goals': {}
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/money')
def money():
    return render_template('money.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# API Endpoints
@app.route('/api/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    db = load_data()
    
    if 'expenses' not in db:
        db['expenses'] = {}
    
    expense_id = str(len(db['expenses']) + 1)
    db['expenses'][expense_id] = {
        'amount': data['amount'],
        'category': data['category'],
        'date': data['date'],
        'description': data['description']
    }
    
    save_data(db)
    return jsonify({'status': 'success'})

@app.route('/api/add_income', methods=['POST'])
def add_income():
    data = request.json
    db = load_data()
    
    if 'incomes' not in db:
        db['incomes'] = {}
    
    income_id = str(len(db['incomes']) + 1)
    db['incomes'][income_id] = {
        'amount': data['amount'],
        'source': data['source'],
        'date': data['date'],
        'description': data['description']
    }
    
    save_data(db)
    return jsonify({'status': 'success'})

@app.route('/api/add_event', methods=['POST'])
def add_event():
    data = request.json
    db = load_data()
    
    if 'events' not in db:
        db['events'] = {}
    
    event_id = str(len(db['events']) + 1)
    db['events'][event_id] = {
        'title': data['title'],
        'start': data['start'],
        'end': data['end'],
        'description': data['description'],
        'recurring': data.get('recurring', False)
    }
    
    save_data(db)
    return jsonify({'status': 'success'})

@app.route('/api/get_expenses')
def get_expenses():
    db = load_data()
    return jsonify(db.get('expenses', {}))

@app.route('/api/get_incomes')
def get_incomes():
    db = load_data()
    return jsonify(db.get('incomes', {}))

@app.route('/api/get_events')
def get_events():
    db = load_data()
    return jsonify(db.get('events', {}))

@app.route('/api/get_financial_summary')
def get_financial_summary():
    db = load_data()
    
    total_income = sum(float(income['amount']) for income in db.get('incomes', {}).values())
    total_expense = sum(float(expense['amount']) for expense in db.get('expenses', {}).values())
    balance = total_income - total_expense
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    })

if __name__ == '__main__':
    app.run(debug=True)