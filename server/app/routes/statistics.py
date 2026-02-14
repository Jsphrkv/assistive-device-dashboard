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

# ✅ REMOVED DUPLICATE - Keep only the parameterized version below
    
@statistics_bp.route('/daily/<int:days>', methods=['GET'])
@token_required
def get_daily_stats(days):
    """
    Get daily statistics for current user
    ✅ FIXED: Now transforms data to match frontend expectations
    """
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        
        supabase = get_supabase()
        
        print(f"📊 Fetching daily stats for user {user_id} (last {days} days)")
        
        # ✅ Query daily_statistics table
        if user_role == 'admin':
            response = supabase.table('daily_statistics')\
                .select('*')\
                .order('stat_date', desc=True)\
                .limit(days)\
                .execute()
        else:
            response = supabase.table('daily_statistics')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('stat_date', desc=True)\
                .limit(days)\
                .execute()
        
        print(f"📊 Found {len(response.data)} daily statistics records")
        
        # ✅ Transform to match chart format
        result = []
        for row in response.data:
            result.append({
                'stat_date': row['stat_date'],  # Keep original
                'date': row['stat_date'],       # For chart
                'total_alerts': row.get('total_alerts', 0),  # Keep original
                'alerts': row.get('total_alerts', 0),        # For chart
                'high': row.get('high_priority', 0),
                'medium': row.get('medium_priority', 0),
                'low': row.get('low_priority', 0)
            })
        
        # Sort by date ascending for chart display
        result.sort(key=lambda x: x['date'])
        
        print(f"✅ Returning {len(result)} days")
        if result:
            print(f"   Sample: {result[0]}")
        
        return jsonify({'data': result}), 200
        
    except Exception as e:
        print(f"❌ Get daily stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@statistics_bp.route('/obstacles', methods=['GET'])
@token_required
def get_obstacle_statistics():
    """
    Get obstacle statistics for current user
    ✅ FIXED: Transforms data correctly for PieChart
    """
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        
        supabase = get_supabase()
        
        print(f"📊 Fetching obstacle stats for user {user_id}")
        
        # ✅ Query obstacle_statistics table
        if user_role == 'admin':
            response = supabase.table('obstacle_statistics')\
                .select('*')\
                .order('total_count', desc=True)\
                .limit(10)\
                .execute()
        else:
            response = supabase.table('obstacle_statistics')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('total_count', desc=True)\
                .limit(10)\
                .execute()
        
        print(f"📊 Found {len(response.data)} obstacle types")
        
        # ✅ Transform to match PieChart format
        result = []
        for row in response.data:
            result.append({
                'obstacle_type': row['obstacle_type'],  # Keep original
                'name': row['obstacle_type'],           # For chart label
                'total_count': row['total_count'],      # Keep original
                'value': row['total_count'],            # For chart value
                'count': row['total_count'],            # Backup
                'percentage': row.get('percentage', 0)
            })
        
        print(f"✅ Returning obstacles:")
        for r in result[:3]:
            print(f"   {r['name']}: {r['value']}")
        
        return jsonify({'data': result}), 200
        
    except Exception as e:
        print(f"❌ Get obstacle statistics error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get obstacle statistics'}), 500


@statistics_bp.route('/hourly', methods=['GET'])
@token_required
def get_hourly_patterns():
    """
    Get hourly detection patterns
    ✅ FIXED: Transforms data correctly for BarChart
    """
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        
        supabase = get_supabase()
        
        print(f"📊 Fetching hourly patterns for user {user_id}")
        
        # ✅ Query hourly_patterns table
        if user_role == 'admin':
            response = supabase.table('hourly_patterns')\
                .select('*')\
                .order('hour_range')\
                .execute()
        else:
            response = supabase.table('hourly_patterns')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('hour_range')\
                .execute()
        
        print(f"📊 Found {len(response.data)} hourly records")
        
        # ✅ Transform to match BarChart format
        result = []
        for row in response.data:
            hour_str = row['hour_range']
            
            result.append({
                'hour_range': hour_str,                      # Keep original
                'hour': hour_str,                            # For chart X-axis
                'detection_count': row.get('detection_count', 0),  # Keep original
                'detections': row.get('detection_count', 0),       # For chart bar height
                'count': row.get('detection_count', 0)       # Backup
            })
        
        # Sort by hour (convert to 24h for sorting)
        def parse_hour(hour_str):
            """Convert '12PM' to 12, '9AM' to 9, etc."""
            try:
                hour_num = int(''.join(filter(str.isdigit, hour_str)))
                if 'PM' in hour_str and hour_num != 12:
                    hour_num += 12
                elif 'AM' in hour_str and hour_num == 12:
                    hour_num = 0
                return hour_num
            except:
                return 0
        
        result.sort(key=lambda x: parse_hour(x['hour']))
        
        print(f"✅ Returning hourly data:")
        for r in result[:5]:
            print(f"   {r['hour']}: {r['detections']} detections")
        
        return jsonify({'data': result}), 200
        
    except Exception as e:
        print(f"❌ Get hourly patterns error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get hourly patterns'}), 500


@statistics_bp.route('/summary', methods=['GET'])
@token_required
def get_ml_statistics():
    """Get ML statistics summary for current user"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        
        supabase = get_supabase()
        
        print(f"📊 Fetching summary stats for user {user_id}")
        
        # ✅ Get user's device IDs first
        user_devices = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        
        device_ids = [device['id'] for device in user_devices.data]
        
        if not device_ids and user_role != 'admin':
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
        
        # ✅ Get total detections count
        if user_role == 'admin':
            total_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .execute()
        else:
            total_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .execute()
        
        total_predictions = total_response.count or 0
        
        # Count anomalies (High/Critical danger levels)
        if user_role == 'admin':
            anomaly_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('danger_level', ['High', 'Critical'])\
                .execute()
        else:
            anomaly_response = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .in_('danger_level', ['High', 'Critical'])\
                .execute()
        
        anomaly_count = anomaly_response.count or 0
        
        # Calculate anomaly rate
        anomaly_rate = (anomaly_count / total_predictions * 100) if total_predictions > 0 else 0
        
        # Severity breakdown
        if user_role == 'admin':
            high_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .eq('danger_level', 'High')\
                .execute().count or 0
            
            medium_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .eq('danger_level', 'Medium')\
                .execute().count or 0
            
            low_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .eq('danger_level', 'Low')\
                .execute().count or 0
        else:
            high_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .eq('danger_level', 'High')\
                .execute().count or 0
            
            medium_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .eq('danger_level', 'Medium')\
                .execute().count or 0
            
            low_count = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .eq('danger_level', 'Low')\
                .execute().count or 0
        
        print(f"✅ Summary: {total_predictions} total, {anomaly_count} anomalies, {anomaly_rate:.1f}% rate")
        
        return jsonify({
            'totalPredictions': total_predictions,
            'anomalyCount': anomaly_count,
            'anomalyRate': round(anomaly_rate, 2),
            'avgAnomalyScore': 67.5,  # TODO: Calculate from actual data
            'severityBreakdown': {
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Get ML statistics error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get ML statistics'}), 500