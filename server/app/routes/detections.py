from flask import Blueprint, request, jsonify, Response
from app.services.supabase_client import get_supabase, get_admin_client
from app.middleware.auth import device_token_required, token_required, check_permission
from app.constants.detection_categories import (
    get_detection_info,
    get_danger_level_from_object,
    get_alert_type_from_object,
    DETECTION_CATEGORIES
)
from datetime import datetime
from app.utils.timezone_helper import now_ph, now_ph_iso, PH_TIMEZONE, utc_to_ph
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
    """Get detection logs with pagination"""
    try:
        user_id = request.current_user['user_id']
        
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        supabase = get_supabase()
        
        # Get user's device
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
        
        # Filter by device_id (which is user-specific)
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
    """Get recent detections (configurable limit, default 10)"""
    try:
        user_id = request.current_user['user_id']
        limit = request.args.get('limit', 10, type=int)
        
        supabase = get_supabase()
        
        # Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'detections': []}), 200
        
        device_id = device.data[0]['id']
        
        # Filter by device_id
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
    """Get detections by date range"""
    try:
        user_id = request.current_user['user_id']
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        supabase = get_supabase()
        
        # Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'data': []}), 200
        
        device_id = device.data[0]['id']
        
        # Filter by device_id and date range
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
    """Get detection count grouped by obstacle type"""
    try:
        user_id = request.current_user['user_id']
        
        supabase = get_supabase()
        
        # Filter by user_id
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
    """Get sensor detection logs for LogsTable.jsx"""
    try:
        user_id = request.current_user['user_id']
        limit = request.args.get('limit', 100, type=int)
        
        supabase = get_supabase()
        
        # Get user's device
        device = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        if not device.data:
            return jsonify({'data': []}), 200
        
        device_id = device.data[0]['id']
        
        # Filter by device_id
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
        format_type = request.args.get('format', 'csv')
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
    try:
        device_id = request.current_device['id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # ✅ FIXED: Use admin client for device operations (bypasses RLS)
        supabase = get_admin_client()
        
        # Get user_id from device
        print(f"🔍 Looking up user for device: {device_id}")
        device_query = supabase.table('user_devices')\
            .select('user_id')\
            .eq('id', device_id)\
            .single()\
            .execute()
        
        if not device_query.data or not device_query.data.get('user_id'):
            print(f"❌ Device has no user_id!")
            return jsonify({'error': 'Device not paired to a user'}), 403
        
        user_id = device_query.data['user_id']
        print(f"✅ Detection from device {device_id} (user: {user_id})")
        
        # Extract detection data - SUPPORT BOTH FIELD NAME FORMATS
        object_detected = data.get('object_detected') or data.get('objectDetected') or 'unknown'
        distance_cm = data.get('distance_cm') or data.get('distanceCm')
        detection_source = data.get('detection_source') or data.get('detectionSource', 'ultrasonic')
        detection_confidence = data.get('detection_confidence') or data.get('detectionConfidence', 85.0)
        
        # Get object classification info
        obj_info = get_detection_info(object_detected)
        
        # Determine danger level and alert type
        if distance_cm:
            danger_level = get_danger_level_from_object(object_detected, distance_cm)
            alert_type = get_alert_type_from_object(object_detected, distance_cm)
        else:
            danger_level = data.get('danger_level') or data.get('dangerLevel', 'Low')
            alert_type = data.get('alert_type') or data.get('alertType', 'Audio')
        
        # Handle image upload
        image_url = None
        if data.get('image_data') or data.get('imageData'):
            try:
                image_data = data.get('image_data') or data.get('imageData')
                image_url = _upload_image_to_supabase(device_id, image_data)
                print(f"✅ Image uploaded: {image_url}")
            except Exception as img_error:
                print(f"⚠️ Image upload failed: {img_error}")

        # Parse numeric fields safely
        raw_distance = data.get('distance_cm') or data.get('distanceCm')
        raw_proximity = data.get('proximity_value') or data.get('proximityValue')
        raw_ambient = data.get('ambient_light') or data.get('ambientLight')
        raw_confidence = data.get('detection_confidence') or data.get('detectionConfidence', 85.0)

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

        # ✅ FIXED: Get timestamp in Philippine time
        detected_at = now_ph_iso()

        # BUILD THE PAYLOAD - FIXED OBSTACLE_TYPE MAPPING
        detection_log = {
            # Required UUID fields
            'user_id': str(user_id),
            'device_id': str(device_id),
            
            # FIXED: Check object_detected FIRST, then fallback to obstacle_type
            'obstacle_type': str(
                data.get('obstacle_type') or 
                data.get('obstacleType') or 
                object_detected or
                obj_info.get('description') or 
                'unknown'
            )[:255],
            
            'object_detected': str(object_detected or 'unknown')[:255],
            'object_category': str(obj_info.get('category') or 'unknown')[:255],
            'danger_level': str(danger_level or 'Low')[:255],
            'alert_type': str(alert_type or 'Audio')[:255],
            'detection_source': str(detection_source or 'ultrasonic')[:255],
            
            # Required timestamp
            'detected_at': str(detected_at),
            
            # Boolean (defaults to False)
            'camera_enabled': bool(data.get('camera_enabled') or data.get('cameraEnabled', False)),
        }
        
        # Optional numeric fields - only add if valid
        if parsed_distance is not None and parsed_distance > 0:
            detection_log['distance_cm'] = float(parsed_distance)
        
        if parsed_proximity is not None and parsed_proximity > 0:
            detection_log['proximity_value'] = int(parsed_proximity)
        
        if parsed_ambient is not None and parsed_ambient > 0:
            detection_log['ambient_light'] = int(parsed_ambient)
        
        if parsed_confidence is not None and parsed_confidence > 0:
            detection_log['detection_confidence'] = float(parsed_confidence)
        
        # Optional text fields
        if image_url:
            detection_log['image_url'] = str(image_url)
        
        print(f"📝 Inserting detection: {object_detected} at {parsed_distance}cm")
        
        # INSERT DETECTION (supabase is already admin client)
        try:
            response = supabase.table('detection_logs')\
                .insert(detection_log)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                print(f"❌ Insert returned no data")
                return jsonify({'error': 'Insert failed'}), 500
            
            detection_id = response.data[0]['id']
            print(f"✅ Detection logged! ID: {detection_id}")
            
        except Exception as db_error:
            print(f"❌ Database insert failed!")
            print(f"   Error: {db_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': 'Database insert failed',
                'details': str(db_error)
            }), 500
        
        # ✅ FIXED: UPDATE LAST_SEEN with Philippine time (supabase is already admin client)
        try:
            print(f"⏰ Updating last_seen for device {device_id}")
            supabase.table('user_devices')\
                .update({
                    'last_seen': now_ph_iso(),
                })\
                .eq('id', device_id)\
                .execute()
            print(f"   ✅ last_seen updated")
        except Exception as e:
            print(f"   ⚠️ last_seen update failed (non-critical): {e}")
        
        # Update statistics (optional)
        try:
            _update_user_statistics_safe(
                user_id=user_id,
                object_detected=object_detected,
                detected_at=detected_at
            )
        except Exception as stats_error:
            print(f"⚠️ Statistics update failed (non-critical): {stats_error}")
        
        # Update device status (optional)
        try:
            _update_device_status_safe(
                device_id=device_id,
                detection_log=detection_log,
                detected_at=detected_at
            )
        except Exception as status_error:
            print(f"⚠️ Device status update failed (non-critical): {status_error}")
        
        return jsonify({
            'message': 'Detection logged successfully',
            'id': detection_id,
            'detection_id': detection_id,
            'object_info': obj_info,
            'image_url': image_url,
            'data': response.data[0]
        }), 201
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ========== STATISTICS UPDATE FUNCTION (UPDATED TO 1-HOUR INTERVALS) ==========

def _update_user_statistics_safe(user_id, object_detected, detected_at):
    """
    Update user-scoped statistics tables
    ✅ USES 1-HOUR INTERVALS and Philippine time
    """
    try:
        from datetime import datetime
        from app.utils.timezone_helper import utc_to_ph, PH_TIMEZONE
        
        supabase = get_admin_client()
        
        # ✅ FIXED: Parse timestamp and convert to Philippine time
        dt = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
        dt_ph = utc_to_ph(dt)
        
        stat_date = dt_ph.date().isoformat()
        hour = dt_ph.hour
        
        # 1-HOUR INTERVAL (12-hour format with AM/PM)
        hour_12 = hour % 12 or 12
        am_pm = 'AM' if hour < 12 else 'PM'
        hour_range = f"{hour_12}{am_pm}"
        
        # 1. Update daily_statistics
        try:
            existing = supabase.table('daily_statistics')\
                .select('id, total_alerts')\
                .eq('user_id', user_id)\
                .eq('stat_date', stat_date)\
                .limit(1)\
                .execute()
            
            if existing.data:
                new_count = existing.data[0]['total_alerts'] + 1
                supabase.table('daily_statistics')\
                    .update({'total_alerts': new_count, 'updated_at': detected_at})\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
                print(f"   ✅ Daily stats updated (count: {new_count})")
            else:
                supabase.table('daily_statistics').insert({
                    'user_id': user_id,
                    'stat_date': stat_date,
                    'total_alerts': 1,
                    'created_at': detected_at
                }).execute()
                print(f"   ✅ Daily stats created")
        except Exception as e:
            print(f"   ⚠️ Daily stats update failed: {e}")
        
        # 2. Update obstacle_statistics
        try:
            existing = supabase.table('obstacle_statistics')\
                .select('id, total_count')\
                .eq('user_id', user_id)\
                .eq('obstacle_type', object_detected)\
                .limit(1)\
                .execute()
            
            if existing.data:
                new_count = existing.data[0]['total_count'] + 1
                supabase.table('obstacle_statistics')\
                    .update({'total_count': new_count, 'updated_at': detected_at})\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
                print(f"   ✅ Obstacle stats updated ({object_detected}: {new_count})")
            else:
                supabase.table('obstacle_statistics').insert({
                    'user_id': user_id,
                    'obstacle_type': object_detected,
                    'total_count': 1,
                    'created_at': detected_at
                }).execute()
                print(f"   ✅ Obstacle stats created ({object_detected})")
        except Exception as e:
            print(f"   ⚠️ Obstacle stats update failed: {e}")
        
        # 3. Update hourly_patterns (NOW WITH 1-HOUR INTERVALS)
        try:
            existing = supabase.table('hourly_patterns')\
                .select('id, detection_count')\
                .eq('user_id', user_id)\
                .eq('hour_range', hour_range)\
                .limit(1)\
                .execute()
            
            if existing.data:
                new_count = existing.data[0]['detection_count'] + 1
                supabase.table('hourly_patterns')\
                    .update({'detection_count': new_count, 'updated_at': detected_at})\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
                print(f"   ✅ Hourly pattern updated ({hour_range}: {new_count})")
            else:
                supabase.table('hourly_patterns').insert({
                    'user_id': user_id,
                    'hour_range': hour_range,
                    'detection_count': 1,
                    'created_at': detected_at
                }).execute()
                print(f"   ✅ Hourly pattern created ({hour_range})")
        except Exception as e:
            print(f"   ⚠️ Hourly pattern update failed: {e}")
        
    except Exception as e:
        print(f"⚠️ Statistics update error (non-critical): {e}")


def _update_device_status_safe(device_id, detection_log, detected_at):
    """Update device status safely - Doesn't fail the request"""
    try:
        supabase = get_admin_client()
        
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
            status_id = status_check.data[0]['id']
            supabase.table('device_status')\
                .update(status_update)\
                .eq('id', status_id)\
                .execute()
        else:
            status_update.update({
                'device_id': device_id,
                'device_online': True,
                'camera_status': 'Active',
                'battery_level': 100
            })
            supabase.table('device_status').insert(status_update).execute()
        
    except Exception as e:
        print(f"⚠️ Device status update error (non-critical): {e}")

# ========== HELPER FUNCTIONS ==========

def _upload_image_to_supabase(device_id, image_base64):
    """Upload detection image to Supabase Storage"""
    try:
        image_data = base64.b64decode(image_base64)
        # ✅ FIXED: Use Philippine time for timestamp
        timestamp = now_ph().strftime('%Y%m%d_%H%M%S')
        filename = f"{device_id}/{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        
        supabase = get_admin_client()
        supabase.storage.from_('detection-image').upload(
            path=filename,
            file=image_data,
            file_options={"content-type": "image/jpeg"}
        )
        
        url = supabase.storage.from_('detection-image').get_public_url(filename)
        return url
    except Exception as e:
        print(f"Image upload error: {e}")
        raise

def _generate_csv(detections):
    """Generate CSV export"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Timestamp', 'Object Detected', 'Category', 'Distance (cm)',
        'Danger Level', 'Alert Type', 'Confidence (%)', 'Source',
        'Proximity', 'Ambient Light'
    ])
    
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
    
    # ✅ FIXED: Use Philippine time for filename
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=detections_{now_ph().strftime("%Y%m%d")}.csv'
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
    
    title = Paragraph("Detection Logs Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
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
    
    data = [['Time', 'Object', 'Category', 'Distance', 'Danger', 'Confidence']]
    for d in detections[:100]:
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
    
    # ✅ FIXED: Use Philippine time for filename
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=detections_{now_ph().strftime("%Y%m%d")}.pdf'
        }
    )