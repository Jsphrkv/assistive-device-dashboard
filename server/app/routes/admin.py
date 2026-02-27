import os
import time
import requests as http_requests
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase, get_admin_client
from app.middleware.auth import token_required, admin_required
from app.utils.timezone_helper import now_ph, now_ph_iso
from datetime import timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ── External service URLs ─────────────────────────────────────────────────────
HF_URL = os.getenv('HF_URL', 'https://josephrkv-capstone2-proj.hf.space')


# ── Shared paginated fetch helpers ────────────────────────────────────────────

def _paginate(query_fn, max_pages=10):
    """
    Execute query_fn(page) in pages of 1000 until exhausted or max_pages hit.
    query_fn receives the page index and returns a Supabase query with
    .range() already applied.
    Bypasses Supabase's server-side 1000-row cap for analytics bulk fetches.
    """
    all_rows = []
    for page in range(max_pages):
        batch = query_fn(page).range(page * 1000, (page + 1) * 1000 - 1).execute().data
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < 1000:
            break
    return all_rows


def _paginate_table(supabase, table, select, filters=None, max_pages=10):
    """
    Convenience wrapper: paginate a single table with optional filters list.
    filters = list of (method, *args) tuples, e.g. [('gte', 'created_at', iso)]
    """
    def query_fn(page):
        q = supabase.table(table).select(select)
        if filters:
            for method, *args in filters:
                q = getattr(q, method)(*args)
        return q.range(page * 1000, (page + 1) * 1000 - 1)

    all_rows = []
    for page in range(max_pages):
        batch = query_fn(page).execute().data
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < 1000:
            break
    return all_rows


# ─────────────────────────────────────────────────────────────────────────────
# 1.  SYSTEM HEALTH  →  AdminSystemHealth.jsx
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/health', methods=['GET'])
@token_required
@admin_required
def get_system_health():
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            hf_future = pool.submit(_ping_service, f"{HF_URL}/health", 15, False)
            ml_future = pool.submit(_fetch_ml_model_status)

        hf_status = hf_future.result()
        ml_models = ml_future.result()

        # Render = always ok — if this code is executing, backend is up
        render_status = {'status': 'ok', 'latencyMs': 0, 'code': 200}

        return jsonify({
            'hfSpace':       hf_status,
            'renderBackend': render_status,
            'mlModels':      ml_models,
        }), 200

    except Exception as e:
        print(f"[Admin Health] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get system health'}), 500


def _ping_service(url, timeout=10, expect_401=False):
    try:
        start = time.time()
        resp  = http_requests.get(url, timeout=timeout)
        ms    = int((time.time() - start) * 1000)
        ok    = resp.status_code < 500 or (expect_401 and resp.status_code == 401)
        return {
            'status':    'ok' if ok else 'error',
            'latencyMs': ms,
            'code':      resp.status_code,
        }
    except http_requests.exceptions.Timeout:
        return {'status': 'error', 'latencyMs': None, 'detail': 'timeout'}
    except Exception as e:
        return {'status': 'error', 'latencyMs': None, 'detail': str(e)}


def _fetch_ml_model_status():
    try:
        resp = http_requests.get(f"{HF_URL}/model-status", timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            result = {}
            for name in ('yolo', 'danger', 'anomaly', 'object', 'environment'):
                m = data.get(name, {})
                result[name] = {
                    'status': 'ok' if m.get('loaded') else 'error',
                    'source': m.get('source', 'unknown'),
                }
            return result
    except Exception as e:
        print(f"[Admin Health] model-status fetch failed: {e}")

    return {
        'yolo':        {'status': 'unknown', 'source': 'yolo_onnx'},
        'danger':      {'status': 'unknown', 'source': 'ml_model'},
        'anomaly':     {'status': 'unknown', 'source': 'ml_model'},
        'object':      {'status': 'unknown', 'source': 'ml_model'},
        'environment': {'status': 'unknown', 'source': 'ml_model'},
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ALL DETECTIONS (cross-user)  →  AdminDetectionLogs.jsx
#     Already server-side paginated at 25/page — no bulk fix needed.
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/detections', methods=['GET'])
@token_required
@admin_required
def get_all_detections():
    try:
        limit      = min(request.args.get('limit',        25,  type=int), 100)
        offset     = request.args.get('offset',       0,     type=int)
        search     = request.args.get('search',       '').strip()
        danger     = request.args.get('danger_level', '').strip()
        start_date = request.args.get('start_date',   '')
        end_date   = request.args.get('end_date',     '')

        supabase = get_admin_client()

        query = supabase.table('detection_logs')\
            .select('*, user_devices!detection_logs_device_id_fkey(device_name, user_id)',
                    count='exact')

        if danger:      query = query.eq('danger_level', danger)
        if start_date:  query = query.gte('detected_at', start_date)
        if end_date:    query = query.lte('detected_at', end_date)
        if search:      query = query.ilike('object_detected', f'%{search}%')

        response = query\
            .order('detected_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

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
#     FIX: All 5 bulk queries now paginate to bypass the 1000-row cap.
#     Before: each query silently returned only 1000 rows → wrong chart data.
#     After:  paginated in chunks of 1000 → correct totals for all time ranges.
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_ml_analytics():
    try:
        days      = min(request.args.get('days', 7, type=int), 90)
        supabase  = get_admin_client()
        end_dt    = now_ph()
        start_dt  = end_dt - timedelta(days=days)
        start_iso = start_dt.isoformat()

        date_filter = [('gte', 'detected_at', start_iso)]

        # ── Total detections (COUNT — always accurate, no cap issue) ─────────
        total_res        = supabase.table('detection_logs')\
            .select('*', count='exact', head=True)\
            .gte('detected_at', start_iso).execute()
        total_detections = total_res.count or 0

        # ── Hourly buckets — paginated ────────────────────────────────────────
        hourly_rows = _paginate_table(
            supabase, 'detection_logs', 'detected_at',
            filters=date_filter,
        )

        hourly_buckets = {}
        for row in hourly_rows:
            ts = row.get('detected_at', '')
            if not ts:
                continue
            try:
                from datetime import datetime
                dt     = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                bucket = dt.strftime('%Y-%m-%d %H:00')
                hourly_buckets[bucket] = hourly_buckets.get(bucket, 0) + 1
            except Exception:
                continue

        hourly_detections = [
            {'hour': k, 'count': v}
            for k, v in sorted(hourly_buckets.items())
        ]

        # ── Object distribution — paginated ───────────────────────────────────
        obj_rows = _paginate_table(
            supabase, 'detection_logs', 'object_detected',
            filters=date_filter,
        )

        obj_counts = {}
        for row in obj_rows:
            obj = row.get('object_detected') or 'unknown'
            obj_counts[obj] = obj_counts.get(obj, 0) + 1

        object_distribution = [
            {'object_type': k, 'count': v}
            for k, v in sorted(obj_counts.items(), key=lambda x: -x[1])
        ]

        # ── Danger frequency — paginated ──────────────────────────────────────
        danger_rows = _paginate_table(
            supabase, 'detection_logs', 'danger_level',
            filters=date_filter,
        )

        danger_counts = {}
        for row in danger_rows:
            lvl = row.get('danger_level') or 'Unknown'
            danger_counts[lvl] = danger_counts.get(lvl, 0) + 1

        danger_frequency = [
            {'danger_level': k, 'count': v}
            for k, v in sorted(danger_counts.items(), key=lambda x: -x[1])
        ]

        # ── Model source ratio — paginated ────────────────────────────────────
        ml_rows = _paginate_table(
            supabase, 'ml_predictions', 'model_source',
            filters=[('gte', 'created_at', start_iso)],
        )

        ml_model_count = 0
        fallback_count = 0
        for row in ml_rows:
            source = row.get('model_source', '')
            if source and 'rules' in source.lower():
                fallback_count += 1
            else:
                ml_model_count += 1

        # ── Avg confidence — paginated ────────────────────────────────────────
        conf_rows = _paginate_table(
            supabase, 'detection_logs', 'detection_confidence',
            filters=date_filter,
        )

        conf_values = [
            r['detection_confidence']
            for r in conf_rows
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
#     Already fine — users/devices are small tables, no cap issue.
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users():
    try:
        supabase = get_admin_client()

        users_res = supabase.table('users')\
            .select('id, username, email, role, created_at, last_login, email_verified')\
            .order('created_at', desc=True)\
            .execute()

        if not users_res.data:
            return jsonify({'users': [], 'total': 0}), 200

        devices_res = supabase.table('user_devices')\
            .select('id, user_id, device_name, device_model, status, last_seen, created_at')\
            .order('created_at', desc=True)\
            .execute()

        devices_by_user = {}
        for d in (devices_res.data or []):
            uid = d['user_id']
            devices_by_user.setdefault(uid, []).append(d)

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
    try:
        limit    = min(request.args.get('limit', 20, type=int), 100)
        supabase = get_admin_client()

        devices_res = supabase.table('user_devices')\
            .select('id').eq('user_id', user_id).execute()

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
    try:
        data       = request.get_json()
        new_status = data.get('status', '').lower()

        if new_status not in ('active', 'inactive'):
            return jsonify({'error': 'status must be "active" or "inactive"'}), 400

        supabase = get_admin_client()

        device_res = supabase.table('user_devices')\
            .select('id, device_name').eq('id', device_id).single().execute()

        if not device_res.data:
            return jsonify({'error': 'Device not found'}), 404

        supabase.table('user_devices')\
            .update({'status': new_status, 'updated_at': now_ph_iso()})\
            .eq('id', device_id).execute()

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
#     Only fetches 30 most recent — no cap issue, no change needed.
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/live-feed', methods=['GET'])
@token_required
@admin_required
def get_live_feed():
    try:
        limit    = min(request.args.get('limit', 30, type=int), 100)
        supabase = get_admin_client()

        response = supabase.table('detection_logs')\
            .select('id, detected_at, object_detected, danger_level, distance_cm, '
                    'detection_confidence, detection_source, '
                    'user_devices!detection_logs_device_id_fkey(device_name)')\
            .order('detected_at', desc=True)\
            .limit(limit)\
            .execute()

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