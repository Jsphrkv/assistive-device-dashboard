
import os
import time
import requests as http_requests
from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase, get_admin_client
from app.middleware.auth import token_required, admin_required
from app.utils.timezone_helper import now_ph, now_ph_iso
from datetime import timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ── External service URLs (set these in your .env) ───────────────────────────
HF_SPACE_URL    = os.getenv('HF_URL', 'https://Josephrkv-capstone2_proj.hf.space')
RENDER_BASE_URL = os.getenv('RENDER_URL', 'https://assistive-device-dashboard.onrender.com')


# ─────────────────────────────────────────────────────────────────────────────
# 1.  SYSTEM HEALTH  →  AdminSystemHealth.jsx
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/health', methods=['GET'])
@token_required
@admin_required
def get_system_health():
    """
    Ping HF Space and Render backend, check ML model status,
    return a single health object for the System Health tab.
    """
    try:
        # ── Ping Hugging Face Space ──────────────────────────────────────────
        hf_status = _ping_service(f"{HF_SPACE_URL}/health")

        # ── Ping Render backend itself (self-check) ──────────────────────────
        render_status = _ping_service(f"{RENDER_BASE_URL}/api/auth/me", expect_401=True)

        # ── Check ML model files via HF /model-status endpoint ───────────────
        # Your ml-service should expose GET /model-status — add it if missing
        # (see _build_ml_status_fallback below for the fallback logic)
        ml_models = _fetch_ml_model_status()

        return jsonify({
            'hfSpace':       hf_status,
            'renderBackend': render_status,
            'mlModels':      ml_models,
        }), 200

    except Exception as e:
        print(f"[Admin Health] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get system health'}), 500


def _ping_service(url, timeout=6, expect_401=False):
    """
    Ping a URL and return a status dict.
    expect_401=True: treat HTTP 401 as 'ok' (auth endpoint responds but rejects no-auth ping).
    """
    try:
        start = time.time()
        resp  = http_requests.get(url, timeout=timeout)
        ms    = int((time.time() - start) * 1000)
        ok    = resp.status_code < 500 or (expect_401 and resp.status_code == 401)
        return {
            'status':    'ok'    if ok else 'error',
            'latencyMs': ms,
            'code':      resp.status_code,
        }
    except http_requests.exceptions.Timeout:
        return {'status': 'error', 'latencyMs': None, 'detail': 'timeout'}
    except Exception as e:
        return {'status': 'error', 'latencyMs': None, 'detail': str(e)}


def _fetch_ml_model_status():
    """
    Try to GET /model-status from HF Space.
    Falls back to a degraded dict if the endpoint doesn't exist yet.

    Expected response from HF Space:
    {
      "yolo":    {"loaded": true,  "source": "yolo_onnx"},
      "danger":  {"loaded": true,  "source": "ml_model"},
      "anomaly": {"loaded": true,  "source": "ml_model"},
      "object":  {"loaded": false, "source": "fallback"}
    }
    """
    try:
        resp = http_requests.get(f"{HF_SPACE_URL}/model-status", timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            result = {}
            for name in ('yolo', 'danger', 'anomaly', 'object'):
                m = data.get(name, {})
                result[name] = {
                    'status': 'ok' if m.get('loaded') else 'error',
                    'source': m.get('source', 'unknown'),
                }
            return result
    except Exception:
        pass  # Fall through to fallback

    # Fallback: endpoint not available — return unknown status
    return {
        'yolo':    {'status': 'unknown', 'source': 'yolo_onnx'},
        'danger':  {'status': 'unknown', 'source': 'ml_model'},
        'anomaly': {'status': 'unknown', 'source': 'ml_model'},
        'object':  {'status': 'unknown', 'source': 'ml_model'},
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ALL DETECTIONS (cross-user)  →  AdminDetectionLogs.jsx
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/detections', methods=['GET'])
@token_required
@admin_required
def get_all_detections():
    """
    Paginated detection_logs across ALL users/devices.
    Supports: limit, offset, search (object name / device name), danger_level,
              start_date, end_date.
    Joins user_devices to include device_name in each row.
    """
    try:
        limit       = request.args.get('limit',       25,    type=int)
        offset      = request.args.get('offset',      0,     type=int)
        search      = request.args.get('search',      '').strip()
        danger      = request.args.get('danger_level', '').strip()
        start_date  = request.args.get('start_date',  '')
        end_date    = request.args.get('end_date',    '')

        # Cap limit to prevent runaway queries
        limit = min(limit, 100)

        supabase = get_admin_client()

        # Build base query — join user_devices for device_name
        query = supabase.table('detection_logs')\
            .select('*, user_devices!detection_logs_device_id_fkey(device_name, user_id)',
                    count='exact')

        if danger:
            query = query.eq('danger_level', danger)
        if start_date:
            query = query.gte('detected_at', start_date)
        if end_date:
            query = query.lte('detected_at', end_date)
        if search:
            # Supabase PostgREST ilike filter on object_detected
            query = query.ilike('object_detected', f'%{search}%')

        response = query\
            .order('detected_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        # Flatten device_name into each row for the frontend table
        detections = []
        for row in (response.data or []):
            device_info = row.pop('user_devices', {}) or {}
            row['device_name'] = device_info.get('device_name', 'Unknown')
            detections.append(row)

        return jsonify({
            'detections': detections,
            'total':      response.count or 0,
            'limit':      limit,
            'offset':     offset,
        }), 200

    except Exception as e:
        print(f"[Admin Detections] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get detections'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 3.  ML ANALYTICS  →  AdminMLAnalytics.jsx
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_ml_analytics():
    """
    Returns hourly detection counts, object type distribution,
    danger level frequency, model source ratio and summary stats
    across ALL users for the last N days.
    """
    try:
        days     = request.args.get('days', 7, type=int)
        days     = min(days, 90)  # cap

        supabase  = get_admin_client()
        end_dt    = now_ph()
        start_dt  = end_dt - timedelta(days=days)
        start_iso = start_dt.isoformat()

        # ── Total detections in window ────────────────────────────────────────
        total_res = supabase.table('detection_logs')\
            .select('*', count='exact', head=True)\
            .gte('detected_at', start_iso)\
            .execute()
        total_detections = total_res.count or 0

        # ── Hourly detections — fetch rows and bucket in Python ───────────────
        # Supabase Python SDK doesn't support GROUP BY directly;
        # we fetch enough rows and aggregate.
        hourly_raw = supabase.table('detection_logs')\
            .select('detected_at')\
            .gte('detected_at', start_iso)\
            .order('detected_at', desc=False)\
            .execute()

        hourly_buckets = {}
        for row in (hourly_raw.data or []):
            ts = row.get('detected_at', '')
            if not ts:
                continue
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                # Bucket key = "YYYY-MM-DD HH:00"
                bucket = dt.strftime('%Y-%m-%d %H:00')
                hourly_buckets[bucket] = hourly_buckets.get(bucket, 0) + 1
            except Exception:
                continue

        hourly_detections = [
            {'hour': k, 'count': v}
            for k, v in sorted(hourly_buckets.items())
        ]

        # ── Object type distribution ──────────────────────────────────────────
        obj_raw = supabase.table('detection_logs')\
            .select('object_detected')\
            .gte('detected_at', start_iso)\
            .execute()

        obj_counts = {}
        for row in (obj_raw.data or []):
            obj = row.get('object_detected') or 'unknown'
            obj_counts[obj] = obj_counts.get(obj, 0) + 1

        object_distribution = [
            {'object_type': k, 'count': v}
            for k, v in sorted(obj_counts.items(), key=lambda x: -x[1])
        ]

        # ── Danger level frequency ────────────────────────────────────────────
        danger_raw = supabase.table('detection_logs')\
            .select('danger_level')\
            .gte('detected_at', start_iso)\
            .execute()

        danger_counts = {}
        for row in (danger_raw.data or []):
            lvl = row.get('danger_level') or 'Unknown'
            danger_counts[lvl] = danger_counts.get(lvl, 0) + 1

        danger_frequency = [
            {'danger_level': k, 'count': v}
            for k, v in sorted(danger_counts.items(), key=lambda x: -x[1])
        ]

        # ── Model source ratio: ml_model vs fallback ──────────────────────────
        # detection_source field stores 'camera' (YOLO), 'ultrasonic', etc.
        # ml_predictions table has model_version to indicate real model vs rules
        ml_source_raw = supabase.table('ml_predictions')\
            .select('model_version')\
            .gte('created_at', start_iso)\
            .execute()

        ml_model_count = 0
        fallback_count = 0
        for row in (ml_source_raw.data or []):
            version = row.get('model_version', '')
            if version and 'rules' in version.lower():
                fallback_count += 1
            else:
                ml_model_count += 1

        # ── Avg confidence ────────────────────────────────────────────────────
        conf_raw = supabase.table('detection_logs')\
            .select('detection_confidence')\
            .gte('detected_at', start_iso)\
            .not_.is_('detection_confidence', 'null')\
            .execute()

        conf_values = [
            r['detection_confidence']
            for r in (conf_raw.data or [])
            if r.get('detection_confidence') is not None
        ]
        avg_confidence = (sum(conf_values) / len(conf_values)) if conf_values else 0.75

        return jsonify({
            'totalDetections':    total_detections,
            'avgConfidence':      round(avg_confidence, 4),
            'hourlyDetections':   hourly_detections,
            'objectDistribution': object_distribution,
            'dangerFrequency':    danger_frequency,
            'modelSourceRatio': {
                'ml_model': ml_model_count,
                'fallback': fallback_count,
            },
        }), 200

    except Exception as e:
        print(f"[Admin Analytics] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get analytics'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 4.  USER & DEVICE MANAGEMENT  →  AdminUserManagement.jsx
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users():
    """
    Return all users with their registered devices.
    Shape: [{ id, username, email, role, devices: [...] }]
    """
    try:
        supabase = get_admin_client()

        # Fetch all users (exclude sensitive fields)
        users_res = supabase.table('users')\
            .select('id, username, email, role, created_at, last_login, email_verified')\
            .order('created_at', desc=True)\
            .execute()

        if not users_res.data:
            return jsonify({'users': [], 'total': 0}), 200

        # Fetch all devices in one query (avoid N+1)
        devices_res = supabase.table('user_devices')\
            .select('id, user_id, device_name, device_model, status, last_seen, created_at')\
            .order('created_at', desc=True)\
            .execute()

        # Group devices by user_id
        devices_by_user = {}
        for d in (devices_res.data or []):
            uid = d['user_id']
            devices_by_user.setdefault(uid, []).append(d)

        # Attach devices to users
        users = []
        for u in users_res.data:
            u['devices'] = devices_by_user.get(u['id'], [])
            users.append(u)

        return jsonify({'users': users, 'total': len(users)}), 200

    except Exception as e:
        print(f"[Admin Users] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get users'}), 500


@admin_bp.route('/users/<user_id>/detections', methods=['GET'])
@token_required
@admin_required
def get_user_detections(user_id):
    """
    Get the last N detections for a specific user (shown in history drawer).
    """
    try:
        limit    = request.args.get('limit', 20, type=int)
        limit    = min(limit, 100)
        supabase = get_admin_client()

        # Get this user's device IDs first
        devices_res = supabase.table('user_devices')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()

        device_ids = [d['id'] for d in (devices_res.data or [])]

        if not device_ids:
            return jsonify({'detections': [], 'total': 0}), 200

        response = supabase.table('detection_logs')\
            .select('id, detected_at, object_detected, danger_level, distance_cm, detection_confidence, detection_source')\
            .in_('device_id', device_ids)\
            .order('detected_at', desc=True)\
            .limit(limit)\
            .execute()

        return jsonify({
            'detections': response.data or [],
            'total':      len(response.data or []),
        }), 200

    except Exception as e:
        print(f"[Admin UserDetections] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get user detections'}), 500


@admin_bp.route('/devices/<device_id>/status', methods=['PATCH'])
@token_required
@admin_required
def toggle_device_status(device_id):
    """
    Toggle a device between active / inactive.
    Body: { "status": "active" | "inactive" }
    """
    try:
        data       = request.get_json()
        new_status = data.get('status', '').lower()

        if new_status not in ('active', 'inactive'):
            return jsonify({'error': 'status must be "active" or "inactive"'}), 400

        supabase = get_admin_client()

        # Verify device exists
        device_res = supabase.table('user_devices')\
            .select('id, device_name')\
            .eq('id', device_id)\
            .single()\
            .execute()

        if not device_res.data:
            return jsonify({'error': 'Device not found'}), 404

        # Update status
        supabase.table('user_devices')\
            .update({'status': new_status, 'updated_at': now_ph_iso()})\
            .eq('id', device_id)\
            .execute()

        return jsonify({
            'message':    f'Device set to {new_status}',
            'device_id':  device_id,
            'new_status': new_status,
        }), 200

    except Exception as e:
        print(f"[Admin ToggleDevice] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to update device status'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 5.  LIVE FEED  →  AdminLiveFeed.jsx  (polled every 3s)
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/live-feed', methods=['GET'])
@token_required
@admin_required
def get_live_feed():
    """
    Returns the N most recent detections across ALL devices.
    Lightweight — used for 3s polling in the live feed tab.
    Joins user_devices for device_name.
    """
    try:
        limit    = request.args.get('limit', 30, type=int)
        limit    = min(limit, 100)
        supabase = get_admin_client()

        response = supabase.table('detection_logs')\
            .select('id, detected_at, object_detected, danger_level, distance_cm, '
                    'detection_confidence, detection_source, '
                    'user_devices!detection_logs_device_id_fkey(device_name)')\
            .order('detected_at', desc=True)\
            .limit(limit)\
            .execute()

        # Flatten device_name
        detections = []
        for row in (response.data or []):
            device_info = row.pop('user_devices', {}) or {}
            row['device_name'] = device_info.get('device_name', 'Unknown')
            detections.append(row)

        return jsonify({
            'detections': detections,
            'total':      len(detections),
            'timestamp':  now_ph_iso(),
        }), 200

    except Exception as e:
        print(f"[Admin LiveFeed] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get live feed'}), 500