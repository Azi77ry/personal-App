from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
from database import db

events_bp = Blueprint('events', __name__)

@events_bp.route('/events')
@login_required
def events_page():
    return render_template('events.html')

# API Routes for Events Management
@events_bp.route('/api/add_event', methods=['POST'])
@login_required
def add_event():
    try:
        data = request.get_json()
        
        # Parse dates properly
        start_date_str = data['start'].split('T')[0] if 'T' in data['start'] else data['start']
        start_time_str = data['start'].split('T')[1] if 'T' in data['start'] else '00:00'
        
        start_datetime = datetime.strptime(f"{start_date_str} {start_time_str}", '%Y-%m-%d %H:%M')
        
        end_datetime = None
        if data.get('end'):
            end_date_str = data['end'].split('T')[0] if 'T' in data['end'] else data['end']
            end_time_str = data['end'].split('T')[1] if 'T' in data['end'] else '00:00'
            end_datetime = datetime.strptime(f"{end_date_str} {end_time_str}", '%Y-%m-%d %H:%M')
        
        event_data = {
            'user_id': current_user.id,
            'title': data['title'],
            'start': start_datetime,
            'end': end_datetime,
            'description': data.get('description', ''),
            'recurring': data.get('recurring', False),
            'recurrence_pattern': data.get('recurrence_pattern'),
            'created_at': datetime.now()
        }
        
        result = db.events.insert_one(event_data)
        return jsonify({'status': 'success', 'message': 'Event added successfully', 'id': str(result.inserted_id)})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error adding event: {str(e)}'}), 500

@events_bp.route('/api/add_task', methods=['POST'])
@login_required
def add_task():
    try:
        data = request.get_json()
        
        task_data = {
            'user_id': current_user.id,
            'name': data['name'],
            'due_date': datetime.strptime(data['due_date'], '%Y-%m-%d'),
            'priority': data.get('priority', 'medium'),
            'description': data.get('description', ''),
            'completed': False,
            'completed_date': None,
            'created_at': datetime.now()
        }
        
        result = db.tasks.insert_one(task_data)
        return jsonify({'status': 'success', 'message': 'Task added successfully', 'id': str(result.inserted_id)})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error adding task: {str(e)}'}), 500

@events_bp.route('/api/get_events')
@login_required
def get_events():
    try:
        events = list(db.events.find({'user_id': current_user.id}).sort('start', 1))
        
        events_list = {}
        for event in events:
            event_id = str(event['_id'])
            events_list[event_id] = {
                'title': event['title'],
                'start': event['start'].isoformat(),
                'end': event['end'].isoformat() if event.get('end') else None,
                'description': event.get('description', ''),
                'recurring': event.get('recurring', False),
                'recurrence_pattern': event.get('recurrence_pattern')
            }
        
        return jsonify(events_list)
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching events: {str(e)}'}), 500

@events_bp.route('/api/get_tasks')
@login_required
def get_tasks():
    try:
        tasks = list(db.tasks.find({'user_id': current_user.id}).sort('due_date', 1))
        
        tasks_list = {}
        for task in tasks:
            task_id = str(task['_id'])
            tasks_list[task_id] = {
                'name': task['name'],
                'due_date': task['due_date'].strftime('%Y-%m-%d'),
                'priority': task.get('priority', 'medium'),
                'description': task.get('description', ''),
                'completed': task.get('completed', False),
                'completed_date': task['completed_date'].strftime('%Y-%m-%d') if task.get('completed_date') else None
            }
        
        return jsonify(tasks_list)
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching tasks: {str(e)}'}), 500

@events_bp.route('/api/update_task/<task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    try:
        data = request.get_json()
        
        update_data = {}
        if 'completed' in data:
            update_data['completed'] = data['completed']
            update_data['completed_date'] = datetime.now() if data['completed'] else None
        
        result = db.tasks.update_one(
            {'_id': ObjectId(task_id), 'user_id': current_user.id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Task updated successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Task not found'}), 404
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating task: {str(e)}'}), 500

@events_bp.route('/api/delete_item/<item_type>/<item_id>', methods=['DELETE'])
@login_required
def delete_event_item(item_type, item_id):
    try:
        collection_map = {
            'events': db.events,
            'tasks': db.tasks
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
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error deleting item: {str(e)}'}), 500