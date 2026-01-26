from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
from app.middleware.auth import check_permission

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

@statistics_bp.route('/daily', methods=['GET'])
@token_required
@check_permission('statistics', 'read')
def get_daily_statistics():
    """Get daily statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        
        supabase = get_supabase()
        response = supabase.table('daily_statistics')\
            .select('*')\
            .order('stat_date', desc=False)\
            .limit(days)\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get daily statistics error: {str(e)}")
        return jsonify({'error': 'Failed to get daily statistics'}), 500

@statistics_bp.route('/obstacles', methods=['GET'])
@token_required
@check_permission('statistics', 'read')
def get_obstacle_statistics():
    """Get obstacle statistics"""
    try:
        supabase = get_supabase()
        response = supabase.table('obstacle_statistics')\
            .select('*')\
            .order('total_count', desc=True)\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get obstacle statistics error: {str(e)}")
        return jsonify({'error': 'Failed to get obstacle statistics'}), 500

@statistics_bp.route('/hourly', methods=['GET'])
@token_required
@check_permission('statistics', 'read')
def get_hourly_patterns():
    """Get hourly detection patterns"""
    try:
        supabase = get_supabase()
        response = supabase.table('hourly_patterns')\
            .select('*')\
            .order('hour_range', desc=False)\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get hourly patterns error: {str(e)}")
        return jsonify({'error': 'Failed to get hourly patterns'}), 500

@statistics_bp.route('/', methods=['GET'])
@token_required
@check_permission('statistics', 'read')
def get_ml_statistics():
    """Get ML statistics for StatisticsTab.jsx"""
    try:
        supabase = get_supabase()
        
        # Get all ML predictions from ml_predictions table
        # (You'll need to create this table or adapt to your schema)
        
        # For now, using detection_logs as example:
        total_response = supabase.table('detection_logs').select('*', count='exact').execute()
        total_predictions = total_response.count
        
        # Count anomalies (high danger = anomaly)
        anomaly_response = supabase.table('detection_logs')\
            .select('*', count='exact')\
            .in_('danger_level', ['High', 'critical'])\
            .execute()
        anomaly_count = anomaly_response.count
        
        # Calculate anomaly rate
        anomaly_rate = (anomaly_count / total_predictions * 100) if total_predictions > 0 else 0
        
        # Average anomaly score (if you have this field)
        # For now, returning a default
        avg_anomaly_score = 67.5
        
        # Severity breakdown
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
        
        return jsonify({
            'totalPredictions': total_predictions,
            'anomalyCount': anomaly_count,
            'anomalyRate': anomaly_rate,
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