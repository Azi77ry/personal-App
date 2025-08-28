from flask import Blueprint, request, jsonify, render_template, send_file
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
import json
from io import BytesIO
from database import db
import bcrypt

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')

@settings_bp.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        update_data = {}
        
        if 'username' in data:
            update_data['username'] = data['username']
        if 'email' in data:
            update_data['email'] = data['email']
        if 'currency' in data:
            update_data['currency'] = data['currency']
        
        db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': update_data}
        )
        
        return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating profile: {str(e)}'}), 500

@settings_bp.route('/api/update_notifications', methods=['POST'])
@login_required
def update_notifications():
    try:
        data = request.get_json()
        notification_settings = {
            'email': data.get('email', True),
            'bills': data.get('bills', True),
            'events': data.get('events', True),
            'time': data.get('time', '09:00')
        }
        
        db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {'notification_settings': notification_settings}}
        )
        
        return jsonify({'status': 'success', 'message': 'Notification settings updated successfully'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating notification settings: {str(e)}'}), 500

@settings_bp.route('/api/get_notification_settings')
@login_required
def get_notification_settings():
    try:
        user_data = db.users.find_one({'_id': ObjectId(current_user.id)})
        notification_settings = user_data.get('notification_settings', {})
        
        return jsonify({
            'status': 'success',
            'settings': {
                'email': notification_settings.get('email', True),
                'bills': notification_settings.get('bills', True),
                'events': notification_settings.get('events', True),
                'time': notification_settings.get('time', '09:00')
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching notification settings: {str(e)}'}), 500

@settings_bp.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data['current_password']
        new_password = data['new_password']
        
        user_data = db.users.find_one({'_id': ObjectId(current_user.id)})
        
        if bcrypt.checkpw(current_password.encode('utf-8'), user_data['password']):
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            db.users.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'password': hashed_password}}
            )
            return jsonify({'status': 'success', 'message': 'Password changed successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 400
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error changing password: {str(e)}'}), 500

@settings_bp.route('/api/export_data')
@login_required
def export_data():
    try:
        # Get all user data
        collections = ['incomes', 'expenses', 'events', 'budgets', 'goals', 'tasks', 'bills']
        user_data = {}
        
        for collection in collections:
            items = list(db[collection].find({'user_id': current_user.id}))
            for item in items:
                item['_id'] = str(item['_id'])
                # Convert dates to strings
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
            user_data[collection] = items
        
        # Create a JSON file in memory
        data_str = json.dumps(user_data, indent=2)
        data_io = BytesIO(data_str.encode('utf-8'))
        data_io.seek(0)
        
        # Send the file
        return send_file(
            data_io,
            as_attachment=True,
            download_name=f'money_event_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
            mimetype='application/json'
        )
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error exporting data: {str(e)}'}), 500

@settings_bp.route('/api/import_data', methods=['POST'])
@login_required
def import_data():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if file and file.filename.endswith('.json'):
            data = json.load(file)
            overwrite = request.form.get('overwrite', 'false').lower() == 'true'
            
            collections = ['incomes', 'expenses', 'events', 'budgets', 'goals', 'tasks', 'bills']
            
            for collection in collections:
                if collection in data:
                    if overwrite:
                        # Delete existing data
                        db[collection].delete_many({'user_id': current_user.id})
                    
                    # Prepare new data with user_id
                    items = data[collection]
                    for item in items:
                        item['user_id'] = current_user.id
                        # Convert string dates back to datetime objects
                        for key, value in item.items():
                            if isinstance(value, str) and 'T' in value:
                                try:
                                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                except:
                                    pass
                    
                    # Insert new data
                    if items:
                        db[collection].insert_many(items)
            
            return jsonify({'status': 'success', 'message': 'Data imported successfully'})
        
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400
    
    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': 'Invalid JSON file'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error importing data: {str(e)}'}), 500

@settings_bp.route('/api/reset_data', methods=['POST'])
@login_required
def reset_data():
    try:
        collections = ['incomes', 'expenses', 'events', 'budgets', 'goals', 'tasks', 'bills']
        
        for collection in collections:
            db[collection].delete_many({'user_id': current_user.id})
        
        return jsonify({'status': 'success', 'message': 'All data has been reset'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error resetting data: {str(e)}'}), 500