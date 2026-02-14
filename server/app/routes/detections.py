from flask import Blueprint, request, jsonify, Response
from app.services.supabase_client import get_supabase
from app.middleware.auth import device_token_required, token_required, check_permission
from app.constants.detection_categories import (
    get_detection_info,
    get_danger_level_from_object,
    get_alert_type_from_object,
    DETECTION_CATEGORIES
)
from datetime import datetime
import base64
import uuid
import csv
from io import StringIO, BytesIO

detections_bp = Blueprint('detections', __name__, url_prefix='/api/detections')

# ========== GET ENDPOINTS (UPDATED WITH USER FILTERING) ==========

@detections_bp.route('/', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_detections():
    """
    Get detection logs with pagination
    ✅ FIXED: Now filters by user_id
    """
    try:
        user_id = request.current_user['user_id']  # ✅ Get user_id from token
        
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        supabase = get_supabase()
        
        # ✅ Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({
                'data': [],
                'count': 0,
                'limit': limit,
                'offset': offset
            }), 200
        
        device_id = device.data[0]['id']
        
        # ✅ Filter by device_id (which is user-specific)
        count_response = supabase.table('detection_logs')\
            .select('*', count='exact')\
            .eq('device_id', device_id)\
            .execute()
        total_count = count_response.count
        
        # Get paginated data
        response = supabase.table('detection_logs')\
            .select('*')\
            .eq('device_id', device_id)\
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
    """
    Get recent detections (configurable limit, default 10)
    ✅ FIXED: Now filters by user_id
    """
    try:
        user_id = request.current_user['user_id']  # ✅ Get user_id
        limit = request.args.get('limit', 10, type=int)
        
        supabase = get_supabase()
        
        # ✅ Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'detections': []}), 200
        
        device_id = device.data[0]['id']
        
        # ✅ Filter by device_id
        response = supabase.table('detection_logs')\
            .select('*')\
            .eq('device_id', device_id)\
            .order('detected_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return jsonify({
            'detections': response.data
        }), 200
        
    except Exception as e:
        print(f"Get recent detections error: {str(e)}")
        return jsonify({'error': 'Failed to get recent detections'}), 500

@detections_bp.route('/by-date', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_detections_by_date():
    """
    Get detections by date range
    ✅ FIXED: Now filters by user_id
    """
    try:
        user_id = request.current_user['user_id']  # ✅ Get user_id
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        supabase = get_supabase()
        
        # ✅ Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'data': []}), 200
        
        device_id = device.data[0]['id']
        
        # ✅ Filter by device_id and date range
        response = supabase.table('detection_logs')\
            .select('*')\
            .eq('device_id', device_id)\
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
    """
    Get detection count grouped by obstacle type
    ✅ FIXED: Now uses user-scoped obstacle_stats
    """
    try:
        user_id = request.current_user['user_id']  # ✅ Get user_id
        
        supabase = get_supabase()
        
        # ✅ Filter by user_id
        response = supabase.table('obstacle_stats')\
            .select('*')\
            .eq('user_id', user_id)\
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
    """
    Get sensor detection logs for LogsTable.jsx
    ✅ FIXED: Now filters by user_id
    """
    try:
        user_id = request.current_user['user_id']  # ✅ Get user_id
        limit = request.args.get('limit', 100, type=int)
        
        supabase = get_supabase()
        
        # ✅ Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'data': []}), 200
        
        device_id = device.data[0]['id']
        
        # ✅ Filter by device_id
        response = supabase.table('detection_logs')\
            .select('*')\
            .eq('device_id', device_id)\
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
                'object_detected': log.get('object_detected'),
                'object_category': log.get('object_category'),
                'distance_cm': log.get('distance_cm'),
                'danger_level': log.get('danger_level'),
                'alert_type': log.get('alert_type'),
                'detection_confidence': log.get('detection_confidence')
            })
        
        return jsonify({'data': formatted_logs}), 200
        
    except Exception as e:
        print(f"Get sensor logs error: {str(e)}")
        return jsonify({'error': 'Failed to get sensor logs'}), 500

@detections_bp.route('/categories', methods=['GET'])
def get_detection_categories():
    """Get all available detection categories"""
    return jsonify({
        'categories': DETECTION_CATEGORIES
    }), 200

@detections_bp.route('/export', methods=['GET'])
@token_required
def export_detections():
    """Export detection logs in various formats (CSV, JSON, PDF)"""
    try:
        user_id = request.current_user['user_id']
        format_type = request.args.get('format', 'csv')  # csv, json, pdf
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        object_filter = request.args.get('object')
        
        supabase = get_supabase()
        
        # Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'error': 'No device found'}), 404
        
        device_id = device.data[0]['id']
        
        # Build query
        query = supabase.table('detection_logs')\
            .select('*')\
            .eq('device_id', device_id)\
            .order('detected_at', desc=True)
        
        if start_date:
            query = query.gte('detected_at', start_date)
        if end_date:
            query = query.lte('detected_at', end_date)
        if object_filter:
            query = query.eq('object_detected', object_filter)
        
        response = query.execute()
        detections = response.data
        
        if format_type == 'json':
            return jsonify({'detections': detections}), 200
        
        elif format_type == 'csv':
            return _generate_csv(detections)
        
        elif format_type == 'pdf':
            return _generate_pdf(detections)
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
        
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': 'Export failed'}), 500

# ========== POST ENDPOINT (UPDATED WITH USER_ID AND STATISTICS) ==========

@detections_bp.route('/', methods=['POST'])
@device_token_required
def log_detection():
    """
    Log a new detection with object classification (called by Raspberry Pi)
    ✅ FIXED: Now includes user_id and updates statistics
    """
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase()
        
        # ✅ NEW: Get user_id from device
        device_query = supabase.table('user_devices')\
            .select('user_id')\
            .eq('id', device_id)\
            .single()\
            .execute()
        
        if not device_query.data:
            return jsonify({'error': 'Device not found'}), 404
        
        user_id = device_query.data['user_id']
        print(f"📍 Detection from device {device_id} (user: {user_id})")
        
        # Extract detection data
        object_detected = data.get('object_detected', 'unknown')
        distance_cm = data.get('distance_cm')
        detection_source = data.get('detection_source', 'ultrasonic')
        detection_confidence = data.get('detection_confidence', 85.0)
        
        # Get object classification info
        obj_info = get_detection_info(object_detected)
        
        # Determine danger level and alert type based on object and distance
        if distance_cm:
            danger_level = get_danger_level_from_object(object_detected, distance_cm)
            alert_type = get_alert_type_from_object(object_detected, distance_cm)
        else:
            danger_level = data.get('danger_level', 'Low')
            alert_type = data.get('alert_type', 'Audio')
        
        # Handle image upload if provided
        image_url = None
        if data.get('image_data'):
            try:
                image_url = _upload_image_to_supabase(device_id, data['image_data'])
                print(f"✅ Image uploaded: {image_url}")
            except Exception as img_error:
                print(f"⚠️ Image upload failed: {img_error}")
                import traceback
                traceback.print_exc()
                # Continue without image - don't fail the whole request
        
        raw_distance = data.get('distance_cm')
        raw_proximity = data.get('proximity_value')
        raw_ambient = data.get('ambient_light')
        raw_confidence = data.get('detection_confidence', 85.0)

        try:
            parsed_distance = float(raw_distance) if raw_distance is not None else None
        except (TypeError, ValueError):
            parsed_distance = None

        try:
            parsed_proximity = int(raw_proximity) if raw_proximity is not None else 0
        except (TypeError, ValueError):
            parsed_proximity = 0

        try:
            parsed_ambient = int(raw_ambient) if raw_ambient is not None else 0
        except (TypeError, ValueError):
            parsed_ambient = 0

        try:
            parsed_confidence = float(raw_confidence) if raw_confidence is not None else 85.0
        except (TypeError, ValueError):
            parsed_confidence = 85.0

        # Get timestamp
        detected_at = datetime.utcnow().isoformat()

        # ✅ PREPARE DETECTION LOG WITH USER_ID
        detection_log = {
            'user_id': user_id,  # ✅ NOW INCLUDES user_id
            'device_id': device_id,
            'obstacle_type': data.get('obstacle_type', obj_info['description']),
            'object_detected': object_detected,
            'object_category': obj_info['category'],
            'distance_cm': parsed_distance,
            'danger_level': danger_level,
            'alert_type': alert_type,
            'proximity_value': parsed_proximity,
            'ambient_light': parsed_ambient,
            'camera_enabled': bool(data.get('camera_enabled', False)),
            'detection_source': detection_source,
            'detection_confidence': parsed_confidence,
            'image_url': image_url,
            'detected_at': detected_at
        }
        
        print(f"🔍 Inserting detection: {detection_log}")
        
        # Insert detection log
        try:
            response = supabase.table('detection_logs').insert(detection_log).execute()
            print(f"✅ Detection logged: {object_detected} ({obj_info['icon']}) at {distance_cm}cm")
        except Exception as db_error:
            print(f"❌ Database insert failed: {db_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Database insert failed: {str(db_error)}'}), 500
        
        if not response.data:
            return jsonify({'error': 'Failed to log detection'}), 500
        
        # ✅ NEW: Update statistics tables
        try:
            _update_user_statistics(
                user_id=user_id,
                object_detected=object_detected,
                detected_at=detected_at
            )
            print(f"✅ Statistics updated for user {user_id}")
        except Exception as stats_error:
            print(f"⚠️ Statistics update failed: {stats_error}")
            # Don't fail the request if statistics update fails
        
        # Update device status with last detection
        try:
            status_check = supabase.table('device_status')\
                .select('id')\
                .eq('device_id', device_id)\
                .limit(1)\
                .execute()
            
            status_update = {
                'last_obstacle': detection_log['obstacle_type'],
                'last_detection_time': detected_at,
                'updated_at': detected_at
            }
            
            if status_check.data and len(status_check.data) > 0:
                # Update existing status
                status_id = status_check.data[0]['id']
                supabase.table('device_status').update(status_update).eq('id', status_id).execute()
            else:
                # Create new status
                status_update.update({
                    'device_id': device_id,
                    'device_online': True,
                    'camera_status': 'Active',
                    'battery_level': 100
                })
                supabase.table('device_status').insert(status_update).execute()
                
            print(f"✅ Device status updated")
        except Exception as status_error:
            print(f"⚠️ Could not update device_status: {status_error}")
            # Don't fail the request if status update fails
        
        return jsonify({
            'message': 'Detection logged successfully',
            'detection_id': response.data[0]['id'],
            'object_info': obj_info,
            'image_url': image_url,
            'data': response.data[0]
        }), 201
        
    except Exception as e:
        print(f"❌ Detection log error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to log detection'}), 500

# ========== STATISTICS UPDATE FUNCTION (NEW) ==========

def _update_user_statistics(user_id, object_detected, detected_at):
    """
    Update user-scoped statistics tables
    ✅ NEW FUNCTION
    
    Updates:
    - daily_stats
    - obstacle_stats  
    - hourly_detection_patterns
    """
    try:
        from datetime import datetime
        
        supabase = get_supabase()
        
        # Parse timestamp
        dt = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
        stat_date = dt.date().isoformat()
        hour = dt.hour
        hour_range = f"{hour}PM" if hour >= 12 else f"{hour}AM"
        
        # 1. Update daily_stats
        try:
            supabase.rpc('upsert_daily_stat', {
                'p_user_id': user_id,
                'p_stat_date': stat_date
            }).execute()
            print(f"   ✅ Daily stats updated")
        except Exception as e:
            print(f"   ⚠️ Daily stats update failed: {e}")
        
        # 2. Update obstacle_stats
        try:
            supabase.rpc('upsert_obstacle_stat', {
                'p_user_id': user_id,
                'p_obstacle_type': object_detected
            }).execute()
            print(f"   ✅ Obstacle stats updated")
        except Exception as e:
            print(f"   ⚠️ Obstacle stats update failed: {e}")
        
        # 3. Update hourly_detection_patterns
        try:
            supabase.rpc('upsert_hourly_pattern', {
                'p_user_id': user_id,
                'p_hour_range': hour_range
            }).execute()
            print(f"   ✅ Hourly pattern updated")
        except Exception as e:
            print(f"   ⚠️ Hourly pattern update failed: {e}")
        
    except Exception as e:
        print(f"❌ Statistics update error: {e}")
        raise

# ========== HELPER FUNCTIONS ==========

def _upload_image_to_supabase(device_id, image_base64):
    """Upload detection image to Supabase Storage"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{device_id}/{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        
        supabase = get_supabase()
        
        # Upload to Supabase Storage
        supabase.storage.from_('detection-image').upload(
            path=filename,
            file=image_data,
            file_options={"content-type": "image/jpeg"}
        )
        
        # Get public URL
        url = supabase.storage.from_('detection-image').get_public_url(filename)
        return url
    except Exception as e:
        print(f"Image upload error: {e}")
        raise

def _generate_csv(detections):
    """Generate CSV export"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Timestamp',
        'Object Detected',
        'Category',
        'Distance (cm)',
        'Danger Level',
        'Alert Type',
        'Confidence (%)',
        'Source',
        'Proximity',
        'Ambient Light'
    ])
    
    # Data rows
    for d in detections:
        writer.writerow([
            d.get('detected_at', ''),
            d.get('object_detected', 'unknown'),
            d.get('object_category', 'unknown'),
            d.get('distance_cm', ''),
            d.get('danger_level', ''),
            d.get('alert_type', ''),
            d.get('detection_confidence', ''),
            d.get('detection_source', ''),
            d.get('proximity_value', ''),
            d.get('ambient_light', '')
        ])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=detections_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )

def _generate_pdf(detections):
    """Generate PDF export"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Detection Logs Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Summary
    total = len(detections)
    critical = len([d for d in detections if d.get('object_category') == 'critical'])
    navigation = len([d for d in detections if d.get('object_category') == 'navigation'])
    environmental = len([d for d in detections if d.get('object_category') == 'environmental'])
    
    summary = Paragraph(
        f"<b>Total Detections:</b> {total}<br/>"
        f"<b>Critical:</b> {critical}<br/>"
        f"<b>Navigation:</b> {navigation}<br/>"
        f"<b>Environmental:</b> {environmental}",
        styles['Normal']
    )
    elements.append(summary)
    elements.append(Spacer(1, 12))
    
    # Table data
    data = [['Time', 'Object', 'Category', 'Distance', 'Danger', 'Confidence']]
    for d in detections[:100]:  # Limit to 100 for PDF
        data.append([
            d.get('detected_at', '')[:16],
            d.get('object_detected', 'unknown')[:15],
            d.get('object_category', 'unknown')[:12],
            f"{d.get('distance_cm', '')} cm" if d.get('distance_cm') else 'N/A',
            d.get('danger_level', '')[:10],
            f"{d.get('detection_confidence', '')}%"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=detections_{datetime.now().strftime("%Y%m%d")}.pdf'
        }
    )