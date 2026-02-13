from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, admin_required
from app.middleware.auth import check_permission

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

def get_user_device_ids(user_id, user_role, supabase):
    """Get device IDs for the current user (or all devices for admin)"""
    if user_role == 'admin':
        return None  # Admin sees everything
    
    user_devices = supabase.table('user_devices')\
        .select('id')\
        .eq('user_id', user_id)\
        .execute()
    
    device_ids = [device['id'] for device in user_devices.data]
    return device_ids if device_ids else ['no-devices']

@statistics_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_statistics():
    """Get daily statistics for current user's devices"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        days = request.args.get('days', 7, type=int)
        
        supabase = get_supabase()
        device_ids = get_user_device_ids(user_id, user_role, supabase)
        
        # If no device IDs (non-admin with no devices), return empty
        if device_ids == ['no-devices']:
            return jsonify({'data': []}), 200
        
        # Get detections grouped by date
        if device_ids is None:  # Admin
            response = supabase.table('detection_logs')\
                .select('detected_at, danger_level, object_category')\
                .order('detected_at', desc=True)\
                .execute()
        else:
            response = supabase.table('detection_logs')\
                .select('detected_at, danger_level, object_category')\
                .in_('device_id', device_ids)\
                .order('detected_at', desc=True)\
                .execute()
        
        # Group by date and calculate stats
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        daily_data = defaultdict(lambda: {'date': None, 'total': 0, 'high': 0, 'medium': 0, 'low': 0})
        
        for log in response.data:
            date_str = log['detected_at'][:10]  # Get YYYY-MM-DD
            daily_data[date_str]['date'] = date_str
            daily_data[date_str]['total'] += 1
            
            if log.get('danger_level') == 'High':
                daily_data[date_str]['high'] += 1
            elif log.get('danger_level') == 'Medium':
                daily_data[date_str]['medium'] += 1
            else:
                daily_data[date_str]['low'] += 1
        
        # Convert to list and sort
        result = sorted(daily_data.values(), key=lambda x: x['date'])[-days:]
        
        return jsonify({'data': result}), 200
        
    except Exception as e:
        print(f"Get daily statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get daily statistics'}), 500


@statistics_bp.route('/obstacles', methods=['GET'])
@token_required
def get_obstacle_statistics():
    """Get obstacle statistics for current user"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        
        if user_role == 'admin':
            response = supabase.table('obstacle_statistics')\
                .select('*')\
                .order('total_count', desc=True)\
                .execute()
        else:
            response = supabase.table('obstacle_statistics')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('total_count', desc=True)\
                .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get obstacle statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get obstacle statistics'}), 500


@statistics_bp.route('/hourly', methods=['GET'])
@token_required
def get_hourly_patterns():
    """Get hourly detection patterns for current user"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        device_ids = get_user_device_ids(user_id, user_role, supabase)
        
        if device_ids == ['no-devices']:
            return jsonify({'data': []}), 200
        
        # Get all detections
        if device_ids is None:  # Admin
            response = supabase.table('detection_logs')\
                .select('detected_at')\
                .execute()
        else:
            response = supabase.table('detection_logs')\
                .select('detected_at')\
                .in_('device_id', device_ids)\
                .execute()
        
        # Group by hour
        from collections import defaultdict
        from datetime import datetime
        
        hourly_data = defaultdict(int)
        
        for log in response.data:
            try:
                dt = datetime.fromisoformat(log['detected_at'].replace('Z', '+00:00'))
                hour = dt.hour
                hourly_data[hour] += 1
            except:
                pass
        
        # Format for chart
        result = [
            {
                'hour': f"{hour:02d}:00",
                'count': hourly_data.get(hour, 0)
            }
            for hour in range(24)
        ]
        
        return jsonify({'data': result}), 200
        
    except Exception as e:
        print(f"Get hourly patterns error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get hourly patterns'}), 500


@statistics_bp.route('/summary', methods=['GET'])
@token_required
def get_ml_statistics():
    """Get ML statistics for current user only"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        supabase = get_supabase()
        
        # ✅ Get user's device IDs first
        user_devices = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        
        device_ids = [device['id'] for device in user_devices.data]
        
        if not device_ids:
            # No devices = no data
            return jsonify({
                'totalPredictions': 0,
                'anomalyCount': 0,
                'anomalyRate': 0,
                'avgAnomalyScore': 0,
                'severityBreakdown': {
                    'high': 0,
                    'medium': 0,
                    'low': 0
                }
            }), 200
        
        # ✅ Filter detection_logs by user's devices
        if user_role == 'admin':
            # Admin sees everything
            total_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .execute()
        else:
            # User sees only their devices' data
            total_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .execute()
        
        total_predictions = total_response.count
        
        # Count anomalies
        if user_role == 'admin':
            anomaly_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('danger_level', ['High', 'critical'])\
                .execute()
        else:
            anomaly_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .in_('danger_level', ['High', 'critical'])\
                .execute()
        
        anomaly_count = anomaly_response.count
        
        # Calculate anomaly rate
        anomaly_rate = (anomaly_count / total_predictions * 100) if total_predictions > 0 else 0
        
        # Average anomaly score
        avg_anomaly_score = 67.5  # TODO: Calculate from actual data
        
        # Severity breakdown
        if user_role == 'admin':
            high_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .eq('danger_level', 'High')\
                .execute().count
            
            medium_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .eq('danger_level', 'Medium')\
                .execute().count
            
            low_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .eq('danger_level', 'Low')\
                .execute().count
        else:
            high_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .eq('danger_level', 'High')\
                .execute().count
            
            medium_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .eq('danger_level', 'Medium')\
                .execute().count
            
            low_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .eq('danger_level', 'Low')\
                .execute().count
        
        return jsonify({
            'totalPredictions': total_predictions,
            'anomalyCount': anomaly_count,
            'anomalyRate': round(anomaly_rate, 2),
            'avgAnomalyScore': avg_anomaly_score,
            'severityBreakdown': {
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            }
        }), 200
        
    except Exception as e:
        print(f"Get ML statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get ML statistics'}), 500