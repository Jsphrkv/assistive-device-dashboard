from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required
from datetime import datetime, timedelta

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@logs_bp.route('/detections', methods=['GET'])
@token_required
def get_detection_logs():
    """Get detection logs for user's device"""
    try:
        user_id = request.current_user['user_id']
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        device_id = request.args.get('device_id')
        log_type = request.args.get('type')
        severity = request.args.get('severity')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        supabase = get_supabase()
        
        # Build query
        query = supabase.table('detection_logs').select('*')
        
        # Filter by user's devices
        if device_id:
            query = query.eq('device_id', device_id)
        else:
            # Get all user's devices
            devices_response = supabase.table('user_devices')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            if devices_response.data:
                device_ids = [d['id'] for d in devices_response.data]
                query = query.in_('device_id', device_ids)
        
        # Apply filters (using your column names)
        if log_type:
            query = query.eq('obstacle_type', log_type)  # ← Your column
        
        if severity:
            query = query.eq('danger_level', severity)  # ← Your column
        
        if start_date:
            query = query.gte('detected_at', start_date)  # ← Your column
        
        if end_date:
            query = query.lte('detected_at', end_date)  # ← Your column
        
        # Order and limit
        query = query.order('detected_at', desc=True).limit(limit)  # ← Your column
        
        response = query.execute()
        
        # ✅ TRANSFORM YOUR COLUMNS TO MATCH FRONTEND EXPECTATIONS
        transformed_data = []
        for item in response.data:
            transformed_data.append({
                'id': item['id'],
                'device_id': item['device_id'],
                'timestamp': item['detected_at'],  # ← Map detected_at to timestamp
                'log_type': item['obstacle_type'],  # ← Map obstacle_type to log_type
                'message': f"{item['obstacle_type']} detected at {item['distance_cm']}cm",  # ← Generate message
                'severity': item['danger_level'],  # ← Map danger_level to severity
                'confidence': 0.85,  # ← Default value
                'is_anomaly': item['danger_level'] == 'high',  # ← Derive from danger_level
                'source': 'device',
                'distance_cm': item['distance_cm'],  # ← Keep original data
                'alert_type': item['alert_type'],  # ← Keep original data
            })
        
        return jsonify({
            'data': transformed_data,
            'count': len(transformed_data)
        }), 200
        
    except Exception as e:
        print(f"Get detection logs error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get detection logs'}), 500


def generate_message(item):
    """Generate a human-readable message from detection data"""
    obstacle = item.get('obstacle_type', 'object')
    distance = item.get('distance_cm')
    danger = item.get('danger_level', 'low')
    
    if distance:
        return f"{obstacle.title()} detected at {distance}cm - {danger.upper()} danger level"
    else:
        return f"{obstacle.title()} detected - {danger.upper()} danger level"


def calculate_anomaly_score(item):
    """Calculate anomaly score from danger level and distance"""
    danger_level = item.get('danger_level', 'low')
    distance = item.get('distance_cm', 100)
    
    # Higher danger = higher anomaly score
    danger_scores = {
        'high': 0.9,
        'medium': 0.6,
        'low': 0.3
    }
    
    base_score = danger_scores.get(danger_level, 0.3)
    
    # Closer distance = higher anomaly score
    if distance and distance < 50:
        base_score += 0.1
    
    return min(base_score, 1.0)


@logs_bp.route('/detections', methods=['POST'])
@device_token_required
def create_detection_log():
    """Create a new detection log (called by Raspberry Pi)"""
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # ✅ MAP INCOMING DATA TO YOUR COLUMN NAMES
        log_entry = {
            'device_id': device_id,
            'detected_at': data.get('timestamp', datetime.utcnow().isoformat()),  # ← timestamp → detected_at
            'obstacle_type': data.get('log_type', data.get('obstacle_type', 'object')),  # ← log_type → obstacle_type
            'distance_cm': data.get('distance_cm', 100),
            'danger_level': data.get('severity', data.get('danger_level', 'low')),  # ← severity → danger_level
            'alert_type': data.get('alert_type', 'both'),
        }
        
        supabase = get_supabase()
        response = supabase.table('detection_logs').insert(log_entry).execute()
        
        return jsonify({
            'message': 'Detection log created',
            'data': response.data[0] if response.data else None
        }), 201
        
    except Exception as e:
        print(f"Create detection log error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create detection log'}), 500


@logs_bp.route('/activity', methods=['GET'])
@token_required
def get_activity_logs():
    """Get activity logs for user"""
    try:
        user_id = request.current_user['user_id']
        limit = request.args.get('limit', 50, type=int)
        
        supabase = get_supabase()
        response = supabase.table('activity_logs')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return jsonify({
            'data': response.data or []
        }), 200
        
    except Exception as e:
        print(f"Get activity logs error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get activity logs'}), 500


@logs_bp.route('/stats', methods=['GET'])
@token_required
def get_log_statistics():
    """Get statistics about detection logs"""
    try:
        user_id = request.current_user['user_id']
        days = request.args.get('days', 7, type=int)
        
        supabase = get_supabase()
        
        # Get user's devices
        devices_response = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        
        if not devices_response.data:
            return jsonify({
                'total': 0,
                'anomalies': 0,
                'activities': 0,
                'maintenance': 0,
                'statistics': 0
            }), 200
        
        device_ids = [d['id'] for d in devices_response.data]
        
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get logs using your column names
        response = supabase.table('detection_logs')\
            .select('*')\
            .in_('device_id', device_ids)\
            .gte('detected_at', start_date)\
            .execute()
        
        logs = response.data or []
        
        # Calculate statistics using your column names
        stats = {
            'total': len(logs),
            'anomalies': len([l for l in logs if l.get('obstacle_type') == 'anomaly']),
            'activities': len([l for l in logs if l.get('obstacle_type') == 'activity']),
            'maintenance': len([l for l in logs if l.get('obstacle_type') == 'maintenance']),
            'statistics': len([l for l in logs if l.get('obstacle_type') == 'statistics']),
            'high_severity': len([l for l in logs if l.get('danger_level') == 'high']),
            'medium_severity': len([l for l in logs if l.get('danger_level') == 'medium']),
            'low_severity': len([l for l in logs if l.get('danger_level') == 'low']),
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"Get log statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get statistics'}), 500