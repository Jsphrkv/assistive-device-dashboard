from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required
from app.middleware.auth import check_permission

detections_bp = Blueprint('detections', __name__, url_prefix='/api/detections')

@detections_bp.route('/', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_detections():
    """Get detection logs with pagination"""
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        supabase = get_supabase()
        
        # Get total count
        count_response = supabase.table('detection_logs').select('*', count='exact').execute()
        total_count = count_response.count
        
        # Get paginated data
        response = supabase.table('detection_logs')\
            .select('*')\
            .order('detected_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return jsonify({
            'data': response.data,
            'count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Get detections error: {str(e)}")
        return jsonify({'error': 'Failed to get detections'}), 500

@detections_bp.route('/recent', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_recent_detections():
    """Get recent detections (last 10)"""
    try:
        supabase = get_supabase()
        response = supabase.table('detection_logs')\
            .select('*')\
            .order('detected_at', desc=True)\
            .limit(10)\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get recent detections error: {str(e)}")
        return jsonify({'error': 'Failed to get recent detections'}), 500

@detections_bp.route('/', methods=['POST'])
@device_token_required
def create_detection():
    """Create new detection log (called by Raspberry Pi)"""
    try:
        data = request.get_json()
        device_id = request.current_device['id']
        
        # Validate required fields
        required_fields = ['obstacle_type', 'distance_cm', 'danger_level', 'alert_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        supabase = get_supabase()
        
        # Insert detection log
        insert_data = {
            'obstacle_type': data['obstacle_type'],
            'distance_cm': data['distance_cm'],
            'danger_level': data['danger_level'],
            'alert_type': data['alert_type'],
            'device_id': device_id  # ← Link to device
        }
        
        response = supabase.table('detection_logs').insert(insert_data).execute()
        
        # Update device status with last obstacle
        try:
            # Check if device_status row exists
            status_check = supabase.table('device_status').select('id').limit(1).execute()
            
            if status_check.data and len(status_check.data) > 0:
                # Update existing row
                status_id = status_check.data[0]['id']
                supabase.table('device_status').update({
                    'last_obstacle': data['obstacle_type'],
                    'last_detection_time': 'now()',
                    'updated_at': 'now()'
                }).eq('id', status_id).execute()
            else:
                # Insert new row if none exists
                supabase.table('device_status').insert({
                    'device_online': True,
                    'camera_status': 'Active',
                    'battery_level': 100,
                    'last_obstacle': data['obstacle_type'],
                    'last_detection_time': 'now()'
                }).execute()
        except Exception as status_error:
            # Don't fail the whole request if status update fails
            print(f"Warning: Could not update device_status: {status_error}")
        
        return jsonify({
            'message': 'Detection logged successfully',
            'data': response.data
        }), 201
        
    except Exception as e:
        print(f"Create detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create detection'}), 500

@detections_bp.route('/by-date', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_detections_by_date():
    """Get detections by date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        supabase = get_supabase()
        response = supabase.table('detection_logs')\
            .select('*')\
            .gte('detected_at', start_date)\
            .lte('detected_at', end_date)\
            .order('detected_at', desc=True)\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get detections by date error: {str(e)}")
        return jsonify({'error': 'Failed to get detections'}), 500

@detections_bp.route('/count-by-type', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_count_by_type():
    """Get detection count grouped by obstacle type"""
    try:
        supabase = get_supabase()
        response = supabase.table('obstacle_statistics')\
            .select('*')\
            .order('total_count', desc=True)\
            .execute()
        
        return jsonify({'data': response.data}), 200
        
    except Exception as e:
        print(f"Get count by type error: {str(e)}")
        return jsonify({'error': 'Failed to get detection count'}), 500