from flask import Blueprint, request, jsonify, Response
from app.services.supabase_client import get_supabase, get_admin_client
from app.middleware.auth import device_token_required, token_required, check_permission
from app.constants.detection_categories import (
    get_detection_info,
    get_danger_level_from_object,
    get_alert_type_from_object,
    DETECTION_CATEGORIES,
)
from datetime import datetime
from app.utils.timezone_helper import now_ph, now_ph_iso, PH_TIMEZONE, utc_to_ph
import base64
import uuid
import csv
from io import StringIO, BytesIO

detections_bp = Blueprint('detections', __name__, url_prefix='/api/detections')

# Max pages × 1000 rows = 5000 — safely covers all sensor/camera logs
_MAX_PAGES = 5


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _get_user_device(supabase, user_id):
    """Return first device ID for user, or None."""
    result = supabase.table('user_devices').select('id').eq('user_id', user_id).limit(1).execute()
    return result.data[0]['id'] if result.data else None


def _paginated_fetch(supabase, device_id, select='*', order_col='detected_at', max_pages=_MAX_PAGES, extra_filters=None):
    """
    Paginate detection_logs in chunks of 1000 to bypass Supabase's server-side
    row cap. Returns all rows up to max_pages * 1000.
    """
    all_rows = []
    for page in range(max_pages):
        q = supabase.table('detection_logs')\
            .select(select)\
            .eq('device_id', device_id)\
            .order(order_col, desc=True)\
            .range(page * 1000, (page + 1) * 1000 - 1)

        if extra_filters:
            for method, *args in extra_filters:
                q = getattr(q, method)(*args)

        batch = q.execute().data
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < 1000:
            break  # last page — no more rows

    return all_rows


# ── GET endpoints ─────────────────────────────────────────────────────────────

@detections_bp.route('/', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_detections():
    """Get detection logs with pagination."""
    try:
        user_id   = request.current_user['user_id']
        limit     = request.args.get('limit', 50, type=int)
        offset    = request.args.get('offset', 0, type=int)
        supabase  = get_supabase()

        device_id = _get_user_device(supabase, user_id)
        if not device_id:
            return jsonify({'data': [], 'count': 0, 'limit': limit, 'offset': offset}), 200

        total = supabase.table('detection_logs')\
            .select('*', count='exact', head=True)\
            .eq('device_id', device_id).execute().count

        rows = supabase.table('detection_logs')\
            .select('*')\
            .eq('device_id', device_id)\
            .order('detected_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute().data

        return jsonify({'data': rows, 'count': total, 'limit': limit, 'offset': offset}), 200

    except Exception as e:
        print(f"Get detections error: {e}")
        return jsonify({'error': 'Failed to get detections'}), 500


@detections_bp.route('/recent', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_recent_detections():
    """
    Get all sensor/camera detection logs via paginated bulk fetch.
    Bypasses Supabase's 1000-row server cap by fetching in chunks of 1000.
    Capped at _MAX_PAGES * 1000 = 5000 rows — enough for all detection_logs.
    """
    try:
        user_id  = request.current_user['user_id']
        supabase = get_supabase()

        device_id = _get_user_device(supabase, user_id)
        if not device_id:
            return jsonify({'detections': []}), 200

        all_rows = _paginated_fetch(supabase, device_id)
        return jsonify({'detections': all_rows}), 200

    except Exception as e:
        print(f"Get recent detections error: {e}")
        return jsonify({'error': 'Failed to get recent detections'}), 500


@detections_bp.route('/by-date', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_detections_by_date():
    """Get detections by date range."""
    try:
        start_date = request.args.get('start_date')
        end_date   = request.args.get('end_date')
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400

        user_id  = request.current_user['user_id']
        supabase = get_supabase()

        device_id = _get_user_device(supabase, user_id)
        if not device_id:
            return jsonify({'data': []}), 200

        rows = _paginated_fetch(
            supabase, device_id,
            extra_filters=[
                ('gte', 'detected_at', start_date),
                ('lte', 'detected_at', end_date),
            ]
        )
        return jsonify({'data': rows}), 200

    except Exception as e:
        print(f"Get detections by date error: {e}")
        return jsonify({'error': 'Failed to get detections'}), 500


@detections_bp.route('/count-by-type', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_count_by_type():
    """Get detection count grouped by obstacle type."""
    try:
        user_id  = request.current_user['user_id']
        supabase = get_supabase()

        rows = supabase.table('obstacle_stats')\
            .select('*').eq('user_id', user_id)\
            .order('total_count', desc=True).execute().data

        return jsonify({'data': rows}), 200

    except Exception as e:
        print(f"Get count by type error: {e}")
        return jsonify({'error': 'Failed to get detection count'}), 500


@detections_bp.route('/sensor/logs', methods=['GET'])
@token_required
@check_permission('detections', 'read')
def get_sensor_logs():
    """
    Get sensor/camera detection logs for LogsTable.jsx.
    Paginated bulk fetch to bypass Supabase's 1000-row server cap.
    """
    try:
        user_id  = request.current_user['user_id']
        supabase = get_supabase()

        device_id = _get_user_device(supabase, user_id)
        if not device_id:
            return jsonify({'data': []}), 200

        select_fields = 'id,detected_at,obstacle_type,object_detected,object_category,distance_cm,danger_level,alert_type,detection_confidence'
        all_rows = _paginated_fetch(supabase, device_id, select=select_fields)

        formatted = [
            {
                'id':                   log.get('id'),
                'detected_at':          log.get('detected_at'),
                'obstacle_type':        log.get('obstacle_type'),
                'object_detected':      log.get('object_detected'),
                'object_category':      log.get('object_category'),
                'distance_cm':          log.get('distance_cm'),
                'danger_level':         log.get('danger_level'),
                'alert_type':           log.get('alert_type'),
                'detection_confidence': log.get('detection_confidence'),
            }
            for log in all_rows
        ]

        return jsonify({'data': formatted}), 200

    except Exception as e:
        print(f"Get sensor logs error: {e}")
        return jsonify({'error': 'Failed to get sensor logs'}), 500


@detections_bp.route('/categories', methods=['GET'])
def get_detection_categories():
    """Get all available detection categories."""
    return jsonify({'categories': DETECTION_CATEGORIES}), 200


@detections_bp.route('/export', methods=['GET'])
@token_required
def export_detections():
    """
    Export detection logs in CSV, JSON, or PDF format.
    Uses paginated fetch to ensure all rows are included in the export.
    """
    try:
        user_id       = request.current_user['user_id']
        format_type   = request.args.get('format', 'csv')
        start_date    = request.args.get('start_date')
        end_date      = request.args.get('end_date')
        object_filter = request.args.get('object')
        supabase      = get_supabase()

        device_id = _get_user_device(supabase, user_id)
        if not device_id:
            return jsonify({'error': 'No device found'}), 404

        extra_filters = []
        if start_date:     extra_filters.append(('gte', 'detected_at', start_date))
        if end_date:       extra_filters.append(('lte', 'detected_at', end_date))
        if object_filter:  extra_filters.append(('eq', 'object_detected', object_filter))

        detections = _paginated_fetch(supabase, device_id, extra_filters=extra_filters or None)

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


# ── POST /api/detections/ ─────────────────────────────────────────────────────

@detections_bp.route('/', methods=['POST'])
@device_token_required
def log_detection():
    try:
        device_id = request.current_device['id']
        data      = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        supabase = get_admin_client()

        # Resolve user_id from device
        print(f"🔍 Looking up user for device: {device_id}")
        device_row = supabase.table('user_devices')\
            .select('user_id').eq('id', device_id).single().execute()

        if not device_row.data or not device_row.data.get('user_id'):
            print("❌ Device has no user_id!")
            return jsonify({'error': 'Device not paired to a user'}), 403

        user_id = device_row.data['user_id']
        print(f"✅ Detection from device {device_id} (user: {user_id})")

        # ── Parse incoming fields (support both snake_case and camelCase) ─────
        def field(*keys, default=None):
            for k in keys:
                if data.get(k) is not None:
                    return data[k]
            return default

        object_detected    = field('object_detected', 'objectDetected', default='unknown')
        raw_distance       = field('distance_cm', 'distanceCm')
        detection_source   = field('detection_source', 'detectionSource', default='ultrasonic')
        raw_confidence = field('detection_confidence', 'detectionConfidence')
        raw_proximity      = field('proximity_value', 'proximityValue', default=0)
        raw_ambient        = field('ambient_light', 'ambientLight', default=0)

        def to_float(v, default=None):
            try: return float(v) if v is not None else default
            except (TypeError, ValueError): return default

        def to_int(v, default=0):
            try: return int(v) if v is not None else default
            except (TypeError, ValueError): return default

        parsed_distance   = to_float(raw_distance)
        parsed_proximity  = to_int(raw_proximity)
        parsed_ambient    = to_int(raw_ambient)
        parsed_confidence = to_float(raw_confidence) 

        obj_info    = get_detection_info(object_detected)
        danger_level = (
            get_danger_level_from_object(object_detected, parsed_distance)
            if parsed_distance else
            field('danger_level', 'dangerLevel', default='Low')
        )
        alert_type = (
            get_alert_type_from_object(object_detected, parsed_distance)
            if parsed_distance else
            field('alert_type', 'alertType', default='Audio')
        )

        # ── Image upload ──────────────────────────────────────────────────────
        image_url = None
        raw_image = field('image_data', 'imageData')
        if raw_image:
            try:
                image_url = _upload_image_to_supabase(device_id, raw_image)
                print(f"✅ Image uploaded: {image_url}")
            except Exception as img_err:
                print(f"⚠️ Image upload failed: {img_err}")

        detected_at = now_ph_iso()

        # ── Build insert payload ──────────────────────────────────────────────
        detection_log = {
            'user_id':          str(user_id),
            'device_id':        str(device_id),
            'obstacle_type':    str(field('obstacle_type', 'obstacleType', default=object_detected) or obj_info.get('description') or 'unknown')[:255],
            'object_detected':  str(object_detected)[:255],
            'object_category':  str(obj_info.get('category') or 'unknown')[:255],
            'danger_level':     str(danger_level or 'Low')[:255],
            'alert_type':       str(alert_type or 'Audio')[:255],
            'detection_source': str(detection_source or 'ultrasonic')[:255],
            'detected_at':      str(detected_at),
            'camera_enabled':   bool(field('camera_enabled', 'cameraEnabled', default=False)),
        }

        if parsed_distance and parsed_distance > 0:
            detection_log['distance_cm'] = float(parsed_distance)
        if parsed_proximity and parsed_proximity > 0:
            detection_log['proximity_value'] = parsed_proximity
        if parsed_ambient and parsed_ambient > 0:
            detection_log['ambient_light'] = parsed_ambient
        if parsed_confidence and parsed_confidence > 0:
            detection_log['detection_confidence'] = float(parsed_confidence)
        if image_url:
            detection_log['image_url'] = str(image_url)

        print(f"📝 Inserting detection: {object_detected} at {parsed_distance}cm")

        # ── DB insert ─────────────────────────────────────────────────────────
        try:
            response = supabase.table('detection_logs').insert(detection_log).execute()
            if not response.data:
                print("❌ Insert returned no data")
                return jsonify({'error': 'Insert failed'}), 500
            detection_id = response.data[0]['id']
            print(f"✅ Detection logged! ID: {detection_id}")
        except Exception as db_err:
            print(f"❌ Database insert failed: {db_err}")
            import traceback; traceback.print_exc()
            return jsonify({'error': 'Database insert failed', 'details': str(db_err)}), 500

        # ── Update last_seen ──────────────────────────────────────────────────
        try:
            supabase.table('user_devices')\
                .update({'last_seen': now_ph_iso()})\
                .eq('id', device_id).execute()
            print("   ✅ last_seen updated")
        except Exception as e:
            print(f"   ⚠️ last_seen update failed (non-critical): {e}")

        # ── Update statistics (non-critical) ──────────────────────────────────
        try:
            _update_user_statistics_safe(user_id, object_detected, detected_at)
        except Exception as e:
            print(f"⚠️ Statistics update failed (non-critical): {e}")

        try:
            _update_device_status_safe(device_id, detection_log, detected_at)
        except Exception as e:
            print(f"⚠️ Device status update failed (non-critical): {e}")

        return jsonify({
            'message':      'Detection logged successfully',
            'id':           detection_id,
            'detection_id': detection_id,
            'object_info':  obj_info,
            'image_url':    image_url,
            'data':         response.data[0],
        }), 201

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── Statistics helpers ────────────────────────────────────────────────────────

def _update_user_statistics_safe(user_id, object_detected, detected_at):
    """Update daily_statistics, obstacle_statistics, and hourly_patterns."""
    try:
        supabase = get_admin_client()

        dt    = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
        dt_ph = utc_to_ph(dt)

        stat_date  = dt_ph.date().isoformat()
        hour       = dt_ph.hour
        hour_12    = hour % 12 or 12
        am_pm      = 'AM' if hour < 12 else 'PM'
        hour_range = f"{hour_12}{am_pm}"

        def upsert_counter(table, match_fields, count_field='total_alerts'):
            """Increment counter or insert new row."""
            q = supabase.table(table).select(f'id, {count_field}')
            for col, val in match_fields.items():
                q = q.eq(col, val)
            existing = q.limit(1).execute()
            if existing.data:
                new_count = existing.data[0][count_field] + 1
                supabase.table(table)\
                    .update({count_field: new_count, 'updated_at': detected_at})\
                    .eq('id', existing.data[0]['id']).execute()
            else:
                supabase.table(table).insert({
                    **match_fields,
                    count_field: 1,
                    'created_at': detected_at,
                }).execute()

        try:
            upsert_counter('daily_statistics',   {'user_id': user_id, 'stat_date': stat_date},       'total_alerts')
            print(f"   ✅ Daily stats updated ({stat_date})")
        except Exception as e:
            print(f"   ⚠️ Daily stats update failed: {e}")

        try:
            upsert_counter('obstacle_statistics', {'user_id': user_id, 'obstacle_type': object_detected}, 'total_count')
            print(f"   ✅ Obstacle stats updated ({object_detected})")
        except Exception as e:
            print(f"   ⚠️ Obstacle stats update failed: {e}")

        try:
            upsert_counter('hourly_patterns',     {'user_id': user_id, 'hour_range': hour_range},    'detection_count')
            print(f"   ✅ Hourly pattern updated ({hour_range})")
        except Exception as e:
            print(f"   ⚠️ Hourly pattern update failed: {e}")

    except Exception as e:
        print(f"⚠️ Statistics update error (non-critical): {e}")


def _update_device_status_safe(device_id, detection_log, detected_at):
    """Update device_status table safely."""
    try:
        supabase     = get_admin_client()
        status_check = supabase.table('device_status')\
            .select('id').eq('device_id', device_id).limit(1).execute()

        update = {
            'last_obstacle':       detection_log['obstacle_type'],
            'last_detection_time': detected_at,
            'updated_at':          detected_at,
        }

        if status_check.data:
            supabase.table('device_status')\
                .update(update).eq('id', status_check.data[0]['id']).execute()
        else:
            supabase.table('device_status').insert({
                **update,
                'device_id':     device_id,
                'device_online': True,
                'camera_status': 'Active',
                'battery_level': 100,
            }).execute()

    except Exception as e:
        print(f"⚠️ Device status update error (non-critical): {e}")


# ── Export helpers ────────────────────────────────────────────────────────────

def _upload_image_to_supabase(device_id, image_base64):
    image_data = base64.b64decode(image_base64)
    timestamp  = now_ph().strftime('%Y%m%d_%H%M%S')
    filename   = f"{device_id}/{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
    supabase   = get_admin_client()
    supabase.storage.from_('detection-image').upload(
        path=filename, file=image_data,
        file_options={"content-type": "image/jpeg"},
    )
    return supabase.storage.from_('detection-image').get_public_url(filename)


def _generate_csv(detections):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Timestamp', 'Object Detected', 'Category', 'Distance (cm)',
        'Danger Level', 'Alert Type', 'Confidence (%)', 'Source',
        'Proximity', 'Ambient Light',
    ])
    for d in detections:
        writer.writerow([
            d.get('detected_at', ''),          d.get('object_detected', 'unknown'),
            d.get('object_category', ''),       d.get('distance_cm', ''),
            d.get('danger_level', ''),          d.get('alert_type', ''),
            d.get('detection_confidence', ''),  d.get('detection_source', ''),
            d.get('proximity_value', ''),       d.get('ambient_light', ''),
        ])
    return Response(
        output.getvalue(), mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=detections_{now_ph().strftime("%Y%m%d")}.csv'},
    )


def _generate_pdf(detections):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Detection Logs Report", styles['Title']), Spacer(1, 12)]

    total         = len(detections)
    critical      = sum(1 for d in detections if d.get('object_category') == 'critical')
    navigation    = sum(1 for d in detections if d.get('object_category') == 'navigation')
    environmental = sum(1 for d in detections if d.get('object_category') == 'environmental')

    elements.append(Paragraph(
        f"<b>Total Detections:</b> {total}<br/><b>Critical:</b> {critical}<br/>"
        f"<b>Navigation:</b> {navigation}<br/><b>Environmental:</b> {environmental}",
        styles['Normal'],
    ))
    elements.append(Spacer(1, 12))

    rows = [['Time', 'Object', 'Category', 'Distance', 'Danger', 'Confidence']]
    for d in detections[:100]:
        rows.append([
            d.get('detected_at', '')[:16],
            d.get('object_detected', 'unknown')[:15],
            d.get('object_category', 'unknown')[:12],
            f"{d.get('distance_cm', '')} cm" if d.get('distance_cm') else 'N/A',
            d.get('danger_level', '')[:10],
            f"{d.get('detection_confidence', '')}%",
        ])

    table = Table(rows)
    table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND',    (0, 1), (-1, -1), colors.beige),
        ('GRID',          (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer.getvalue(), mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=detections_{now_ph().strftime("%Y%m%d")}.pdf'},
    )