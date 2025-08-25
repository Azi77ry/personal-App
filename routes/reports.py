from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
from database import db

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@reports_bp.route('/api/get_goals')
@login_required
def get_goals():
    goals = list(db.goals.find({'user_id': current_user.id}))
    for goal in goals:
        goal['_id'] = str(goal['_id'])
        if goal.get('target_date'):
            goal['target_date'] = goal['target_date'].strftime('%Y-%m-%d')
    return jsonify(goals)

@reports_bp.route('/api/add_goal', methods=['POST'])
@login_required
def add_goal():
    data = request.get_json()
    goal_data = {
        'user_id': current_user.id,
        'name': data['name'],
        'target_amount': float(data['target_amount']),
        'current_amount': float(data.get('current_amount', 0)),
        'target_date': datetime.strptime(data['target_date'], '%Y-%m-%d') if data.get('target_date') else None,
        'created_at': datetime.now()
    }
    db.goals.insert_one(goal_data)
    return jsonify({'status': 'success', 'message': 'Goal added successfully'})