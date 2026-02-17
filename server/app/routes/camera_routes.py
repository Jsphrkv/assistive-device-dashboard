"""
Camera Routes - Snapshot upload and retrieval
Add this as a new file: app/routes/camera_routes.py
Then register it in your app/__init__.py
"""

from flask import Blueprint, request, jsonify
import base64
import os
from datetime import datetime
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required

camera_bp = Blueprint('camera', __name__, url_prefix='/api/camera')

# Load Supabase config from environment
SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
SNAPSHOT_BUCKET = 'camera'


@camera_bp.route('/upload', methods=['POST'])
def upload_snapshot():
    """
    Pi sends base64 image → backend decodes → uploads to Supabase Storage
    Uses device token auth (same as status updates)
    """
    try:
        device_token = request.headers.get('X-Device-Token')
        if not device_token:
            return jsonify({'error': 'Device token required'}), 401
        
        data = request.get_json()
        image_data = data.get('imageData')
        
        if not image_data:
            return jsonify({'error': 'imageData required'}), 400
        
        # Decode base64 to bytes
        try:
            jpeg_bytes = base64.b64decode(image_data)
        except Exception as e:
            return jsonify({'error': f'Invalid base64: {str(e)}'}), 400
        
        supabase = get_supabase()
        
        # Get device_id from token
        device_response = supabase.table('user_devices')\
            .select('device_id, user_id')\
            .eq('device_token', device_token)\
            .limit(1)\
            .execute()
        
        if not device_response.data:
            return jsonify({'error': 'Invalid device token'}), 401
        
        device_id = device_response.data[0]['device_id']
        
        # Upload to Supabase Storage
        file_path = f"{device_id}/latest.jpg"
        
        try:
            # Use Supabase Storage API
            import requests
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{SNAPSHOT_BUCKET}/{file_path}"
            
            upload_response = requests.put(
                upload_url,
                data=jpeg_bytes,
                headers={
                    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                    'Content-Type': 'image/jpeg',
                    'x-upsert': 'true'  # Overwrite if exists
                },
                timeout=15
            )
            
            if upload_response.status_code not in [200, 201]:
                print(f"Supabase upload error: {upload_response.status_code} - {upload_response.text}")
                return jsonify({'error': 'Failed to upload to storage'}), 500
            
        except Exception as e:
            print(f"Storage upload exception: {str(e)}")
            return jsonify({'error': f'Storage error: {str(e)}'}), 500
        
        # Build public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SNAPSHOT_BUCKET}/{file_path}"
        
        # Update DB with snapshot URL
        supabase.table('user_devices')\
            .update({
                'camera_snapshot_url': public_url,
                'snapshot_updated_at': datetime.now().isoformat()
            })\
            .eq('device_token', device_token)\
            .execute()
        
        return jsonify({
            'message': 'Snapshot uploaded successfully',
            'url': public_url
        }), 200
        
    except Exception as e:
        print(f"Upload snapshot error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to upload snapshot'}), 500


@camera_bp.route('/snapshot', methods=['GET'])
@token_required
def get_snapshot():
    """
    Dashboard calls this to get the latest snapshot URL
    Returns the URL stored in user_devices
    """
    try:
        user_id = request.current_user['user_id']
        supabase = get_supabase()
        
        response = supabase.table('user_devices')\
            .select('camera_snapshot_url, snapshot_updated_at, device_name')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not response.data:
            return jsonify({
                'data': {
                    'snapshotUrl': None,
                    'updatedAt': None
                }
            }), 200
        
        device = response.data[0]
        
        return jsonify({
            'data': {
                'snapshotUrl': device.get('camera_snapshot_url'),
                'updatedAt': device.get('snapshot_updated_at'),
                'deviceName': device.get('device_name')
            }
        }), 200
        
    except Exception as e:
        print(f"Get snapshot error: {str(e)}")
        return jsonify({'error': 'Failed to get snapshot'}), 500