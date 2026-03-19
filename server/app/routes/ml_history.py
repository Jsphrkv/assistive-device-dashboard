from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from app.utils.timezone_helper import now_ph, now_ph_iso, PH_TIMEZONE, utc_to_ph

ml_history_bp = Blueprint('ml_history', __name__, url_prefix='/api/ml-history')

# ── Shared helpers ────────────────────────────────────────────────────────────

def _get_device_ids(supabase, user_id, user_role):
    if user_role == 'admin':
        return None
    result = supabase.table('user_devices').select('id').eq('user_id', user_id).execute()
    return [d['id'] for d in result.data] or []

def _apply_device_filter(query, device_ids, col='device_id'):
    if device_ids:
        query = query.in_(col, device_ids)
    return query

def _safe_float(val, default=None):
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def _normalize_confidence(v):
    if v is None:
        return None
    v = float(v)
    if v <= 0.01:
        return None
    if v > 1:
        v = v / 100
    return v


def _to_ph_iso(ts_str):
    """
    FIX: Convert UTC ISO timestamp (from Supabase ml_predictions.created_at)
    to Philippine Time (UTC+8) ISO string.

    ml_predictions.created_at is stored as UTC by Supabase's default.
    detection_logs.detected_at is already PH time via now_ph_iso().
    Without this conversion, anomaly timestamps appear ~8 hours behind
    detection timestamps on the dashboard.
    """
    if not ts_str:
        return ts_str
    try:
        s = ts_str.strip()
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        elif '+' not in s and len(s) == 19:
            s = s + '+00:00'
        dt_utc = datetime.fromisoformat(s)
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return utc_to_ph(dt_utc).isoformat()
    except Exception as e:
        print(f"[ml_history] _to_ph_iso failed for '{ts_str}': {e}")
        return ts_str


# ── GET /api/ml-history ───────────────────────────────────────────────────────

@ml_history_bp.route('', methods=['GET'])
@token_required
def get_ml_history():
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']

        limit      = min(request.args.get('limit', 1000, type=int), 1000)
        offset     = request.args.get('offset', 0, type=int)
        pred_type  = request.args.get('type')
        source     = request.args.get('source', 'all')
        anom_only  = request.args.get('anomalies_only', 'false').lower() == 'true'
        start_date = request.args.get('start_date')
        end_date   = request.args.get('end_date')

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({'data': [], 'total': 0, 'limit': limit, 'offset': offset}), 200

        combined = []

        # ── ml_predictions ────────────────────────────────────────────────────
        if source in ('all', 'predictions'):
            q = supabase.table('ml_predictions').select('*, user_devices(device_name)')
            q = _apply_device_filter(q, device_ids)

            if pred_type:
                type_map = {
                    'detection':   'object_detection',
                    'danger':      'danger_prediction',
                    'environment': 'environment_classification',
                    'anomaly':     'anomaly',
                }
                q = q.eq('prediction_type', type_map.get(pred_type, pred_type))

            if anom_only:  q = q.eq('is_anomaly', True)
            if start_date: q = q.gte('created_at', start_date)
            if end_date:   q = q.lte('created_at', end_date)

            for item in q.order('created_at', desc=True).limit(limit).execute().data:
                pt         = item.get('prediction_type', 'unknown')
                result     = {}
                confidence = None

                if pt == 'anomaly':
                    health     = _safe_float(item.get('device_health_score'), 0)
                    score      = _safe_float(item.get('anomaly_score'))
                    is_anomaly = item.get('is_anomaly', False)
                    message    = (
                        f"Device anomaly detected (health: {health:.1f}%)"
                        if is_anomaly
                        else f"Device health: {health:.1f}%"
                    )
                    result     = {
                        'score':               score,
                        'severity':            item.get('anomaly_severity'),
                        'device_health_score': health,
                        'message':             message,
                    }
                    confidence = _normalize_confidence(score)

                elif pt == 'object_detection':
                    obj  = item.get('object_detected', 'object')
                    dist = item.get('distance_cm', 0)
                    conf = item.get('detection_confidence')
                    result = {
                        'object':       obj, 'obstacle_type': obj,
                        'distance':     dist, 'distance_cm':  dist,
                        'danger_level': item.get('danger_level'),
                        'confidence':   conf,
                    }
                    confidence = _normalize_confidence(conf)

                elif pt == 'danger_prediction':
                    score  = _safe_float(item.get('danger_score'), 0)
                    action = item.get('recommended_action', 'UNKNOWN')
                    result = {
                        'danger_score':       score,
                        'recommended_action': action,
                        'time_to_collision':  item.get('time_to_collision'),
                        'message':            f"{action} - Danger score: {score:.1f}",
                    }
                    confidence = _normalize_confidence(score / 100) if score > 0 else None

                elif pt == 'environment_classification':
                    env   = item.get('environment_type', 'unknown')
                    light = item.get('lighting_condition', 'unknown')
                    result = {
                        'environment_type':   env,
                        'lighting_condition': light,
                        'complexity_level':   item.get('complexity_level'),
                        'message':            f"{env} - {light} lighting",
                    }
                    confidence = _normalize_confidence(item.get('detection_confidence'))

                combined.append({
                    'id':               item['id'],
                    'device_id':        item['device_id'],
                    'device_name':      (item.get('user_devices') or {}).get('device_name', 'Unknown'),
                    'prediction_type':  pt,
                    'is_anomaly':       item.get('is_anomaly', False),
                    'confidence_score': confidence,
                    # FIX: convert UTC → PH time so timestamps align with detection_logs
                    'timestamp':        _to_ph_iso(item['created_at']),
                    'result':           result,
                    'source':           'ml_prediction',
                })

        # ── detection_logs ────────────────────────────────────────────────────
        if source in ('all', 'detections') and pred_type in (None, 'detection'):
            q = supabase.table('detection_logs')\
                .select('*, user_devices!detection_logs_device_id_fkey(device_name)')
            q = _apply_device_filter(q, device_ids)

            if anom_only:  q = q.eq('danger_level', 'High')
            if start_date: q = q.gte('detected_at', start_date)
            if end_date:   q = q.lte('detected_at', end_date)

            for item in q.order('detected_at', desc=True).limit(limit).execute().data:
                combined.append({
                    'id':               item['id'],
                    'device_id':        item['device_id'],
                    'device_name':      (item.get('user_devices') or {}).get('device_name', 'Unknown'),
                    'prediction_type':  'detection',
                    'is_anomaly':       item['danger_level'] == 'High',
                    'confidence_score': _normalize_confidence(item.get('detection_confidence')),
                    # detection_logs.detected_at is already PH time — no conversion needed
                    'timestamp':        item['detected_at'],
                    'result': {
                        'obstacle_type': item['obstacle_type'],
                        'distance':      item['distance_cm'],
                        'distance_cm':   item['distance_cm'],
                        'danger_level':  item['danger_level'],
                        'alert_type':    item.get('alert_type'),
                    },
                    'source': 'detection_log',
                })

        combined.sort(key=lambda x: x['timestamp'], reverse=True)

        real_total = 0
        try:
            if source in ('all', 'predictions'):
                q = supabase.table('ml_predictions').select('*', count='exact', head=True)
                q = _apply_device_filter(q, device_ids)
                if anom_only: q = q.eq('is_anomaly', True)
                real_total += q.execute().count or 0

            if source in ('all', 'detections') and pred_type in (None, 'detection'):
                q = supabase.table('detection_logs').select('*', count='exact', head=True)
                q = _apply_device_filter(q, device_ids)
                if anom_only: q = q.eq('danger_level', 'High')
                real_total += q.execute().count or 0
        except Exception as e:
            print(f"⚠️ Total count error: {e}")
            real_total = len(combined)

        return jsonify({
            'data':    combined[offset:offset + limit],
            'total':   real_total,
            'fetched': len(combined),
            'limit':   limit,
            'offset':  offset,
        }), 200

    except Exception as e:
        print(f"Get ML history error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get ML history'}), 500


# ── GET /api/ml-history/anomalies ─────────────────────────────────────────────

@ml_history_bp.route('/anomalies', methods=['GET'])
@token_required
def get_anomalies():
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']
        limit     = request.args.get('limit', 20, type=int)

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({'data': []}), 200

        combined = []

        q = supabase.table('ml_predictions')\
            .select('*, user_devices(device_name)')\
            .eq('is_anomaly', True)\
            .order('created_at', desc=True)\
            .limit(limit)
        q = _apply_device_filter(q, device_ids)

        for item in q.execute().data:
            pt       = item.get('prediction_type', 'unknown')
            score    = None
            severity = 'medium'
            message  = 'Anomaly detected'

            if pt == 'anomaly':
                health   = _safe_float(item.get('device_health_score'), 0)
                score    = _normalize_confidence(item.get('anomaly_score'))
                severity = item.get('anomaly_severity', 'medium')
                message  = f"Device anomaly detected (health: {health:.1f}%)"

            elif pt == 'danger_prediction':
                raw_score = _safe_float(item.get('danger_score'), 0)
                score     = _normalize_confidence(raw_score / 100) if raw_score > 0 else None
                action    = item.get('recommended_action', 'UNKNOWN')
                severity  = 'high' if (raw_score or 0) > 70 else 'medium'
                message   = f"Danger detected - {action} recommended"

            elif pt == 'object_detection':
                score    = _normalize_confidence(item.get('detection_confidence'))
                danger   = item.get('danger_level', 'low')
                severity = danger.lower()
                obj      = item.get('object_detected', 'object')
                dist     = item.get('distance_cm', 0)
                message  = f"{obj.capitalize()} detected at {dist}cm"

            combined.append({
                'id':          item['id'],
                'device_id':   item['device_id'],
                'device_name': (item.get('user_devices') or {}).get('device_name', 'Unknown'),
                'type':        pt,
                'severity':    severity,
                'message':     message,
                'score':       score,
                # FIX: Convert UTC → PH time for correct display
                'timestamp':   _to_ph_iso(item['created_at']),
                'source':      'ml_prediction',
            })

        combined.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'data': combined[:limit]}), 200

    except Exception as e:
        print(f"Get anomalies error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get anomalies'}), 500


# ── GET /api/ml-history/device-health ────────────────────────────────────────
# NEW: Device health derived from detection patterns in detection_logs.
# Replaces the broken battery-based health that always showed 0% on Pi
# because powerbank battery level is unreadable via software.
#
# Health score = 100 - (critical_rate * 60) - (high_rate * 30) - confidence_penalty
# A device that mostly sees Low/Medium danger with high confidence = healthy.
# A device with frequent Critical detections or low confidence = degraded.

@ml_history_bp.route('/device-health', methods=['GET'])
@token_required
def get_device_health():
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({'health_score': 100, 'status': 'No device', 'details': {}}), 200

        end_dt    = now_ph()
        start_iso = (end_dt - timedelta(hours=24)).isoformat()

        # Fetch last 24h detection_logs
        q = supabase.table('detection_logs')\
            .select('danger_level, detection_confidence, detected_at, object_detected')\
            .gte('detected_at', start_iso)\
            .order('detected_at', desc=True)
        q = _apply_device_filter(q, device_ids)
        rows = q.execute().data

        # Also get device last_seen
        last_seen = None
        try:
            dq = supabase.table('user_devices').select('last_seen, device_name')
            dq = _apply_device_filter(dq, device_ids)
            dev = dq.limit(1).execute().data
            if dev:
                last_seen = dev[0].get('last_seen')
        except Exception:
            pass

        total = len(rows)

        if total == 0:
            # No recent detections — device may be offline but not "unhealthy"
            return jsonify({
                'health_score':   85,
                'status':         'Idle',
                'status_color':   'yellow',
                'last_seen':      last_seen,
                'details': {
                    'total_detections_24h': 0,
                    'critical_count':       0,
                    'high_count':           0,
                    'medium_count':         0,
                    'low_count':            0,
                    'critical_rate_pct':    0,
                    'avg_confidence_pct':   0,
                    'message':              'No detections in last 24h — device may be idle',
                },
            }), 200

        critical_count = sum(1 for r in rows if r.get('danger_level') == 'Critical')
        high_count     = sum(1 for r in rows if r.get('danger_level') == 'High')
        medium_count   = sum(1 for r in rows if r.get('danger_level') == 'Medium')
        low_count      = sum(1 for r in rows if r.get('danger_level') == 'Low')

        critical_rate = critical_count / total
        high_rate     = high_count     / total

        conf_vals = [
            float(r['detection_confidence'])
            for r in rows
            if r.get('detection_confidence') is not None
        ]
        avg_conf = (sum(conf_vals) / len(conf_vals)) if conf_vals else 0.65

        # Health formula:
        # Start at 100, deduct for high danger rates and low confidence
        # Critical detections are expected for an assistive device — not a flaw.
        # Penalise only if >80% of detections are Critical (sensor may be stuck).
        conf_penalty    = max(0.0, (0.50 - avg_conf) * 40)   # penalty if avg conf < 50%
        critical_penalty = max(0.0, (critical_rate - 0.80) * 60)  # penalty if >80% critical
        high_penalty    = max(0.0, (high_rate - 0.70) * 30)

        health_score = max(0.0, min(100.0,
            100.0 - conf_penalty - critical_penalty - high_penalty
        ))
        health_score = round(health_score, 1)

        if health_score >= 80:
            status       = 'Good'
            status_color = 'green'
        elif health_score >= 60:
            status       = 'Fair'
            status_color = 'yellow'
        elif health_score >= 40:
            status       = 'Degraded'
            status_color = 'orange'
        else:
            status       = 'Poor'
            status_color = 'red'

        return jsonify({
            'health_score':   health_score,
            'status':         status,
            'status_color':   status_color,
            'last_seen':      last_seen,
            'details': {
                'total_detections_24h': total,
                'critical_count':       critical_count,
                'high_count':           high_count,
                'medium_count':         medium_count,
                'low_count':            low_count,
                'critical_rate_pct':    round(critical_rate * 100, 1),
                'avg_confidence_pct':   round(avg_conf * 100, 1),
                'message': f"{total} detections in last 24h · avg confidence {avg_conf*100:.0f}%",
            },
        }), 200

    except Exception as e:
        print(f"Get device health error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get device health'}), 500


# ── GET /api/ml-history/stats ─────────────────────────────────────────────────

@ml_history_bp.route('/stats', methods=['GET'])
@token_required
def get_ml_stats():
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']
        days      = request.args.get('days', 7, type=int)

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({
                'totalPredictions': 0, 'anomalyCount': 0,
                'anomalyRate': 0, 'avgConfidence': 0,
                'byType': {}, 'bySource': {},
            }), 200

        end_dt    = now_ph()
        start_iso = (end_dt - timedelta(days=days)).isoformat()

        def ml_count(extra=None):
            q = supabase.table('ml_predictions')\
                .select('*', count='exact', head=True)\
                .gte('created_at', start_iso)
            q = _apply_device_filter(q, device_ids)
            if extra:
                for col, val in extra.items():
                    q = q.in_(col, val) if isinstance(val, list) else q.eq(col, val)
            return q.execute().count or 0

        def det_count(extra=None):
            q = supabase.table('detection_logs')\
                .select('*', count='exact', head=True)\
                .gte('detected_at', start_iso)
            q = _apply_device_filter(q, device_ids)
            if extra:
                for col, val in extra.items():
                    q = q.in_(col, val) if isinstance(val, list) else q.eq(col, val)
            return q.execute().count or 0

        ml_total      = ml_count()
        det_total     = det_count()
        ml_anomalies  = ml_count({'is_anomaly': True})
        det_anomalies = det_count({'danger_level': 'High'})

        total     = ml_total + det_total
        anomalies = ml_anomalies + det_anomalies
        anom_rate = (anomalies / total * 100) if total > 0 else 0

        by_type = {
            'anomaly':                    ml_count({'prediction_type': 'anomaly'}),
            'object_detection':           ml_count({'prediction_type': 'object_detection'}),
            'danger_prediction':          ml_count({'prediction_type': 'danger_prediction'}),
            'environment_classification': ml_count({'prediction_type': 'environment_classification'}),
            'detection':                  det_total,
        }

        conf_scores = []
        try:
            q = supabase.table('ml_predictions')\
                .select('prediction_type, anomaly_score, detection_confidence, danger_score')\
                .gte('created_at', start_iso)
            q = _apply_device_filter(q, device_ids)
            for pred in q.execute().data:
                pt = pred.get('prediction_type')
                if pt == 'anomaly' and pred.get('anomaly_score') is not None:
                    v = _normalize_confidence(pred['anomaly_score'])
                    if v: conf_scores.append(v)
                elif pt == 'object_detection' and pred.get('detection_confidence') is not None:
                    v = _normalize_confidence(pred['detection_confidence'])
                    if v: conf_scores.append(v)
                elif pt == 'danger_prediction' and pred.get('danger_score') is not None:
                    v = _normalize_confidence(pred['danger_score'] / 100)
                    if v: conf_scores.append(v)
                elif pt == 'environment_classification' and pred.get('detection_confidence') is not None:
                    v = _normalize_confidence(pred['detection_confidence'])
                    if v: conf_scores.append(v)
        except Exception as ce:
            print(f"⚠️ Confidence fetch error: {ce}")

        try:
            q = supabase.table('detection_logs')\
                .select('detection_confidence')\
                .gte('detected_at', start_iso)
            q = _apply_device_filter(q, device_ids)
            for row in q.execute().data:
                v = _normalize_confidence(row.get('detection_confidence'))
                if v: conf_scores.append(v)
        except Exception as ce:
            print(f"⚠️ Detection confidence fetch error: {ce}")

        avg_conf = (sum(conf_scores) / len(conf_scores)) if conf_scores else 0.0

        return jsonify({
            'totalPredictions': total,
            'anomalyCount':     anomalies,
            'anomalyRate':      round(anom_rate, 2),
            'avgConfidence':    round(avg_conf * 100, 2),
            'byType':           by_type,
            'bySource':         {'ml_predictions': ml_total, 'detection_logs': det_total},
        }), 200

    except Exception as e:
        print(f"Get ML stats error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get ML stats'}), 500


# ── GET /api/ml-history/daily-summary ────────────────────────────────────────

@ml_history_bp.route('/daily-summary', methods=['GET'])
@token_required
def get_daily_summary():
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']
        days      = request.args.get('days', 7, type=int)

        if days not in (7, 30, 90):
            days = 7

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({'data': []}), 200

        end_dt    = now_ph()
        start_dt  = end_dt - timedelta(days=days)
        start_iso = start_dt.isoformat()
        end_iso   = end_dt.isoformat()

        ml_rows = []
        page = 0
        while True:
            q = supabase.table('ml_predictions')\
                .select('created_at, prediction_type, is_anomaly, detection_confidence, anomaly_score, danger_score')\
                .gte('created_at', start_iso)\
                .lte('created_at', end_iso)
            q = _apply_device_filter(q, device_ids)
            batch = q.range(page * 1000, (page + 1) * 1000 - 1).execute().data
            if not batch:
                break
            ml_rows.extend(batch)
            if len(batch) < 1000:
                break
            page += 1

        det_rows = []
        page = 0
        while True:
            q = supabase.table('detection_logs')\
                .select('detected_at, danger_level, detection_confidence')\
                .gte('detected_at', start_iso)\
                .lte('detected_at', end_iso)
            q = _apply_device_filter(q, device_ids)
            batch = q.range(page * 1000, (page + 1) * 1000 - 1).execute().data
            if not batch:
                break
            det_rows.extend(batch)
            if len(batch) < 1000:
                break
            page += 1

        daily      = defaultdict(lambda: defaultdict(int))
        daily_conf = defaultdict(list)

        for row in ml_rows:
            # FIX: convert UTC created_at → PH time before extracting date
            # so daily buckets use PH calendar days not UTC days
            ph_ts = _to_ph_iso(row['created_at'])
            day   = ph_ts[:10]
            pt    = row.get('prediction_type', '')
            daily[day][pt]         += 1
            daily[day]['ml_total'] += 1
            if row.get('is_anomaly'):
                daily[day]['ml_anomaly'] += 1

            if pt == 'anomaly' and row.get('anomaly_score'):
                v = _normalize_confidence(row['anomaly_score'])
                if v: daily_conf[day].append(v)
            elif pt == 'object_detection' and row.get('detection_confidence'):
                v = _normalize_confidence(row['detection_confidence'])
                if v: daily_conf[day].append(v)
            elif pt == 'danger_prediction' and row.get('danger_score'):
                v = _normalize_confidence(row['danger_score'] / 100)
                if v: daily_conf[day].append(v)
            elif pt == 'environment_classification' and row.get('detection_confidence'):
                v = _normalize_confidence(row['detection_confidence'])
                if v: daily_conf[day].append(v)

        for row in det_rows:
            # detection_logs.detected_at is already PH time
            day = row['detected_at'][:10]
            daily[day]['det_total'] += 1
            if row.get('danger_level') == 'High':
                daily[day]['det_anomaly'] += 1
            if row.get('detection_confidence'):
                v = _normalize_confidence(row['detection_confidence'])
                if v: daily_conf[day].append(v)

        result = []
        for i in range(days):
            day_dt  = start_dt + timedelta(days=i)
            day_key = day_dt.strftime('%Y-%m-%d')
            d       = daily[day_key]

            count_obj    = d['object_detection']
            count_danger = d['danger_prediction']
            count_det    = d['det_total']
            total        = d['ml_total'] + count_det
            anomalies    = d['ml_anomaly'] + d['det_anomaly']

            conf_list      = daily_conf[day_key]
            avg_confidence = round(
                (sum(conf_list) / len(conf_list)) * 100, 2
            ) if conf_list else 0.0

            result.append({
                'date_iso':           day_key,
                'date':               day_dt.strftime('%b %-d'),
                'anomalies':          anomalies,
                'detections':         count_obj + count_det,
                'danger_predictions': count_danger,
                'avg_confidence':     avg_confidence,
                'total_logs':         total,
            })

        return jsonify({'data': result}), 200

    except Exception as e:
        print(f"Get daily summary error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get daily summary'}), 500
    
# ── ADD THIS ROUTE to ml_history_bp.py on Render ─────────────────────────────
# Paste this entire block inside ml_history_bp.py, just before the final
# get_daily_summary route. No other changes to that file needed.
# ─────────────────────────────────────────────────────────────────────────────

@ml_history_bp.route('/detection-anomalies', methods=['GET'])
@token_required
def get_detection_anomalies():
    """
    Compute anomaly signals from detection_logs patterns — NOT hardware telemetry.
    The Pi uses a powerbank so battery/hardware metrics are unreliable.
    Instead, anomalies are derived from what the device is actually detecting:

    Signal 1 — Critical spike:   >60% of last 20 detections are Critical danger
    Signal 2 — Confidence drop:  avg confidence of last 20 detections < 40%
    Signal 3 — Detection flood:  detection rate in last 10min > 2x previous 10min
    Signal 4 — Pattern shift:    dominant object type changed between last 5 vs prev 15
    """
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({'anomalies': [], 'is_anomaly': False, 'summary': 'No device paired'}), 200

        # Fetch last 20 detections for pattern analysis
        q = supabase.table('detection_logs')\
            .select('danger_level, detection_confidence, object_detected, detected_at')\
            .order('detected_at', desc=True)\
            .limit(20)
        q = _apply_device_filter(q, device_ids)
        rows = q.execute().data

        if not rows:
            return jsonify({
                'anomalies':  [],
                'is_anomaly': False,
                'summary':    'No recent detections to analyze',
                'stats': {
                    'total_analyzed':    0,
                    'critical_count':    0,
                    'critical_rate_pct': 0,
                    'avg_confidence_pct':0,
                    'dominant_object':   None,
                    'pattern_shift':     False,
                },
            }), 200

        total = len(rows)
        anomalies = []

        # ── Signal 1: Critical spike ──────────────────────────────────────────
        critical_rows  = [r for r in rows if r.get('danger_level') == 'Critical']
        critical_rate  = len(critical_rows) / total
        if critical_rate > 0.60:
            anomalies.append({
                'type':     'critical_spike',
                'severity': 'high' if critical_rate > 0.80 else 'medium',
                'message':  f"Critical spike — {len(critical_rows)}/{total} recent detections Critical",
                'value':    round(critical_rate * 100, 1),
            })

        # ── Signal 2: Confidence drop ─────────────────────────────────────────
        conf_vals = [
            float(r['detection_confidence'])
            for r in rows
            if r.get('detection_confidence') is not None
        ]
        avg_conf = (sum(conf_vals) / len(conf_vals)) if conf_vals else None
        if avg_conf is not None and avg_conf < 0.40:
            anomalies.append({
                'type':     'confidence_drop',
                'severity': 'high' if avg_conf < 0.20 else 'medium',
                'message':  f"Low confidence — avg {avg_conf*100:.0f}% across last {total} detections",
                'value':    round(avg_conf * 100, 1),
            })

        # ── Signal 3: Detection flood ─────────────────────────────────────────
        # Compare count in last 10 min vs previous 10 min
        try:
            end_dt        = now_ph()
            cutoff_recent = (end_dt - timedelta(minutes=10)).isoformat()
            cutoff_prev   = (end_dt - timedelta(minutes=20)).isoformat()

            def _count_window(start_iso, end_iso):
                q2 = supabase.table('detection_logs')\
                    .select('*', count='exact', head=True)\
                    .gte('detected_at', start_iso)\
                    .lte('detected_at', end_iso)
                q2 = _apply_device_filter(q2, device_ids)
                return q2.execute().count or 0

            recent_count = _count_window(cutoff_recent, end_dt.isoformat())
            prev_count   = _count_window(cutoff_prev, cutoff_recent)

            if prev_count > 0 and recent_count > prev_count * 2 and recent_count >= 5:
                anomalies.append({
                    'type':     'detection_flood',
                    'severity': 'medium',
                    'message':  f"Detection flood — {recent_count} detections in last 10min (prev: {prev_count})",
                    'value':    recent_count,
                })
        except Exception as e:
            print(f"[detection-anomalies] flood check failed (non-critical): {e}")

        # ── Signal 4: Pattern shift ───────────────────────────────────────────
        # Compare dominant object in last 5 vs previous 15
        recent_5 = rows[:5]
        prev_15  = rows[5:20]

        def _dominant(group):
            if not group:
                return None
            counts = {}
            for r in group:
                obj = r.get('object_detected') or 'unknown'
                counts[obj] = counts.get(obj, 0) + 1
            return max(counts, key=counts.get)

        dom_recent = _dominant(recent_5)
        dom_prev   = _dominant(prev_15)

        pattern_shift = (
            dom_recent is not None and
            dom_prev   is not None and
            dom_recent != dom_prev
        )
        if pattern_shift:
            anomalies.append({
                'type':     'pattern_shift',
                'severity': 'low',
                'message':  f"Environment shift — {dom_prev} → {dom_recent} in last 5 detections",
                'value':    f"{dom_prev}→{dom_recent}",
            })

        # ── Overall anomaly flag ──────────────────────────────────────────────
        has_high   = any(a['severity'] == 'high'   for a in anomalies)
        has_medium = any(a['severity'] == 'medium' for a in anomalies)
        is_anomaly = bool(anomalies)
        overall_severity = (
            'high'   if has_high   else
            'medium' if has_medium else
            'low'    if anomalies  else
            'normal'
        )

        if not anomalies:
            summary = f"Normal — {total} recent detections look healthy"
        elif len(anomalies) == 1:
            summary = anomalies[0]['message']
        else:
            summary = f"{len(anomalies)} anomaly signals detected"

        return jsonify({
            'anomalies':        anomalies,
            'is_anomaly':       is_anomaly,
            'overall_severity': overall_severity,
            'summary':          summary,
            'stats': {
                'total_analyzed':    total,
                'critical_count':    len(critical_rows),
                'critical_rate_pct': round(critical_rate * 100, 1),
                'avg_confidence_pct':round(avg_conf * 100, 1) if avg_conf is not None else None,
                'dominant_object':   dom_recent,
                'pattern_shift':     pattern_shift,
            },
            'timestamp': now_ph_iso(),
        }), 200

    except Exception as e:
        print(f"Get detection anomalies error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get detection anomalies'}), 500