from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, device_token_required
from app.middleware.auth import check_permission
import base64
import uuid
from datetime import datetime

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
        
        # Handle image upload to Supabase Storage
        image_url = None
        if 'image_data' in data and data['image_data']:
            try:
                # Decode base64 image
                image_bytes = base64.b64decode(data['image_data'])
                
                # Generate unique filename: device_id/timestamp_uuid.jpg
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_id}/{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
                
                # Upload to Supabase Storage
                upload_response = supabase.storage.from_('detection-image').upload(
                    path=filename,
                    file=image_bytes,
                    file_options={"content-type": "image/jpeg"}
                )
                
                # Get public URL
                image_url = supabase.storage.from_('detection-image').get_public_url(filename)
                
                print(f"✅ Image uploaded: {filename}")
                print(f"✅ Image URL: {image_url}")  # ← ADD THIS to see the URL
                
            except Exception as img_error:
                print(f"⚠️ Image upload failed: {img_error}")
                import traceback
                traceback.print_exc()  # ← ADD THIS to see full error
                # Continue without image - don't fail the whole request
        
        # Insert detection log with image_url
        insert_data = {
            'obstacle_type': data['obstacle_type'],
            'distance_cm': float(data['distance_cm']),  # ← Ensure it's a float
            'danger_level': data['danger_level'],
            'alert_type': data['alert_type'],
            'device_id': device_id,
            'proximity_value': int(data.get('proximity_value', 0)),  # ← Ensure it's an int
            'ambient_light': int(data.get('ambient_light', 0)),  # ← Ensure it's an int
            'camera_enabled': bool(data.get('camera_enabled', False)),  # ← Ensure it's a bool
            'image_url': image_url  # Store URL
        }
        
        print(f"🔍 Inserting data: {insert_data}")  # ← ADD THIS to see what's being inserted
        
        # TRY THE INSERT WITH BETTER ERROR HANDLING
        try:
            response = supabase.table('detection_logs').insert(insert_data).execute()
            print(f"✅ Database insert successful")  # ← ADD THIS
        except Exception as db_error:
            print(f"❌ Database insert failed: {db_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Database insert failed: {str(db_error)}'}), 500
        
        # Update device status with last obstacle
        try:
            status_check = supabase.table('device_status').select('id').limit(1).execute()
            
            if status_check.data and len(status_check.data) > 0:
                status_id = status_check.data[0]['id']
                supabase.table('device_status').update({
                    'last_obstacle': data['obstacle_type'],
                    'last_detection_time': datetime.utcnow().isoformat(),  # ✅ Correct
                    'updated_at': datetime.utcnow().isoformat()  # ✅ Correct
                }).eq('id', status_id).execute()
            else:
                supabase.table('device_status').insert({
                    'device_online': True,
                    'camera_status': 'Active',
                    'battery_level': 100,
                    'last_obstacle': data['obstacle_type'],
                    'last_detection_time': datetime.utcnow().isoformat()  # ✅ Correct
                }).execute()
        except Exception as status_error:
            print(f"Warning: Could not update device_status: {status_error}")
        
        # MAKE SURE THIS RETURN IS PROPERLY INDENTED
        return jsonify({
            'data': response.data,
            'image_url': image_url
        }), 201
        
    except Exception as e:
        print(f"❌ Create detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create detection: {str(e)}'}), 500

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
    
@detections_bp.route('/sensor/logs', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_sensor_logs():
    """Get sensor detection logs for LogsTable.jsx"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        supabase = get_supabase()
        response = supabase.table('detection_logs')\
            .select('*')\
            .order('detected_at', desc=True)\
            .limit(limit)\
            .execute()
        
        # Transform data to match LogsTable.jsx format
        formatted_logs = []
        for log in response.data:
            formatted_logs.append({
                'id': log.get('id'),
                'detected_at': log.get('detected_at'),
                'obstacle_type': log.get('obstacle_type'),
                'distance_cm': log.get('distance_cm'),
                'danger_level': log.get('danger_level'),
                'alert_type': log.get('alert_type')
            })
        
        return jsonify({'data': formatted_logs}), 200
        
    except Exception as e:
        print(f"Get sensor logs error: {str(e)}")
        return jsonify({'error': 'Failed to get sensor logs'}), 500