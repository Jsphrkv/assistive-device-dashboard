from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, admin_required
from app.middleware.auth import check_permission

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

@statistics_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_statistics():
    """Get daily statistics for current user's devices"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        days = request.args.get('days', 7, type=int)
        
        supabase = get_supabase()
        
        # ✅ Admins see all data, users see only their own
        if user_role == 'admin':
            response = supabase.table('daily_statistics')\
                .select('*')\
                .order('stat_date', desc=False)\
                .limit(days)\
                .execute()
        else:
            # ✅ Filter by user_id if the table has it
            response = supabase.table('daily_statistics')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('stat_date', desc=False)\
                .limit(days)\
                .execute()
        
        return jsonify({'data': response.data}), 200
        
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
        
        if user_role == 'admin':
            response = supabase.table('hourly_patterns')\
                .select('*')\
                .order('hour_range', desc=False)\
                .execute()
        else:
            response = supabase.table('hourly_patterns')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('hour_range', desc=False)\
                .execute()
        
        return jsonify({'data': response.data}), 200
        
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