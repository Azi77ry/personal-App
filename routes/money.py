from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
from database import db

money_bp = Blueprint('money', __name__)

@money_bp.route('/money')
@login_required
def money_page():
    return render_template('money.html')

# API Routes for Money Management
@money_bp.route('/api/add_income', methods=['POST'])
@login_required
def add_income():
    data = request.get_json()
    income_data = {
        'user_id': current_user.id,
        'amount': float(data['amount']),
        'source': data['source'],
        'date': datetime.strptime(data['date'], '%Y-%m-%d'),
        'description': data.get('description', ''),
        'created_at': datetime.now()
    }
    db.incomes.insert_one(income_data)
    return jsonify({'status': 'success', 'message': 'Income added successfully'})

# ... rest of the money routes ...

@money_bp.route('/api/add_expense', methods=['POST'])
@login_required
def add_expense():
    data = request.get_json()
    expense_data = {
        'user_id': current_user.id,
        'amount': float(data['amount']),
        'category': data['category'],
        'date': datetime.strptime(data['date'], '%Y-%m-%d'),
        'description': data.get('description', ''),
        'created_at': datetime.now()
    }
    db.expenses.insert_one(expense_data)
    return jsonify({'status': 'success', 'message': 'Expense added successfully'})

@money_bp.route('/api/add_budget', methods=['POST'])
@login_required
def add_budget():
    data = request.get_json()
    budget_data = {
        'user_id': current_user.id,
        'category': data['category'],
        'amount': float(data['amount']),
        'month': data['month'],
        'created_at': datetime.now()
    }
    db.budgets.insert_one(budget_data)
    return jsonify({'status': 'success', 'message': 'Budget set successfully'})

@money_bp.route('/api/add_bill', methods=['POST'])
@login_required
def add_bill():
    data = request.get_json()
    bill_data = {
        'user_id': current_user.id,
        'name': data['name'],
        'amount': float(data['amount']),
        'due_date': datetime.strptime(data['due_date'], '%Y-%m-%d'),
        'recurring': data['recurring'],
        'paid': False,
        'created_at': datetime.now()
    }
    db.bills.insert_one(bill_data)
    return jsonify({'status': 'success', 'message': 'Bill added successfully'})

@money_bp.route('/api/get_incomes')
@login_required
def get_incomes():
    incomes = list(db.incomes.find({'user_id': current_user.id}).sort('date', -1))
    # Convert ObjectId to string for JSON serialization
    for income in incomes:
        income['_id'] = str(income['_id'])
        income['date'] = income['date'].strftime('%Y-%m-%d')
        income['created_at'] = income['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(incomes)

@money_bp.route('/api/get_expenses')
@login_required
def get_expenses():
    expenses = list(db.expenses.find({'user_id': current_user.id}).sort('date', -1))
    for expense in expenses:
        expense['_id'] = str(expense['_id'])
        expense['date'] = expense['date'].strftime('%Y-%m-%d')
        expense['created_at'] = expense['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(expenses)

@money_bp.route('/api/get_budgets')
@login_required
def get_budgets():
    budgets = list(db.budgets.find({'user_id': current_user.id}))
    for budget in budgets:
        budget['_id'] = str(budget['_id'])
    return jsonify(budgets)

@money_bp.route('/api/get_bills')
@login_required
def get_bills():
    bills = list(db.bills.find({'user_id': current_user.id}).sort('due_date', 1))
    for bill in bills:
        bill['_id'] = str(bill['_id'])
        bill['due_date'] = bill['due_date'].strftime('%Y-%m-%d')
        bill['created_at'] = bill['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(bills)

@money_bp.route('/api/get_financial_summary')
@login_required
def get_financial_summary():
    # Calculate total income
    pipeline_income = [
        {'$match': {'user_id': current_user.id}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    income_result = list(db.incomes.aggregate(pipeline_income))
    total_income = income_result[0]['total'] if income_result else 0
    
    # Calculate total expenses
    pipeline_expense = [
        {'$match': {'user_id': current_user.id}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    expense_result = list(db.expenses.aggregate(pipeline_expense))
    total_expense = expense_result[0]['total'] if expense_result else 0
    
    # Calculate balance
    balance = total_income - total_expense
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance
    })

@money_bp.route('/api/delete_item/<item_type>/<item_id>', methods=['DELETE'])
@login_required
def delete_item(item_type, item_id):
    collection_map = {
        'incomes': db.incomes,
        'expenses': db.expenses,
        'bills': db.bills,
        'budgets': db.budgets
    }
    
    if item_type not in collection_map:
        return jsonify({'status': 'error', 'message': 'Invalid item type'}), 400
    
    result = collection_map[item_type].delete_one({
        '_id': ObjectId(item_id),
        'user_id': current_user.id
    })
    
    if result.deleted_count > 0:
        return jsonify({'status': 'success', 'message': 'Item deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Item not found'}), 404