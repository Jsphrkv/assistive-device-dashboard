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

@statistics_bp.route('/summary', methods=['GET'])
@token_required
@check_permission('statistics', 'read')
def get_summary():
    """Get overall summary statistics"""
    try:
        supabase = get_supabase()
        
        # Get total detections
        total_response = supabase.table('detection_logs').select('*', count='exact').execute()
        total_detections = total_response.count
        
        # Get detections today
        today_response = supabase.table('detection_logs')\
            .select('*', count='exact')\
            .gte('detected_at', 'today')\
            .execute()
        today_detections = today_response.count
        
        # Get most common obstacle
        obstacles_response = supabase.table('obstacle_statistics')\
            .select('*')\
            .order('total_count', desc=True)\
            .limit(1)\
            .execute()
        
        most_common = obstacles_response.data[0] if obstacles_response.data else None
        
        # Get high danger count
        high_danger_response = supabase.table('detection_logs')\
            .select('*', count='exact')\
            .eq('danger_level', 'High')\
            .execute()
        high_danger_count = high_danger_response.count
        
        return jsonify({
            'totalDetections': total_detections,
            'todayDetections': today_detections,
            'mostCommonObstacle': most_common['obstacle_type'] if most_common else None,
            'highDangerCount': high_danger_count
        }), 200
        
    except Exception as e:
        print(f"Get summary error: {str(e)}")
        return jsonify({'error': 'Failed to get summary'}), 500