from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
from datetime import datetime, timedelta
from collections import defaultdict
from app.utils.timezone_helper import now_ph, now_ph_iso, PH_TIMEZONE, utc_to_ph

ml_history_bp = Blueprint('ml_history', __name__, url_prefix='/api/ml-history')

# ── Shared helpers ────────────────────────────────────────────────────────────

def _get_device_ids(supabase, user_id, user_role):
    """Return list of device UUIDs for this user, or None for admin (all devices)."""
    if user_role == 'admin':
        return None
    result = supabase.table('user_devices').select('id').eq('user_id', user_id).execute()
    return [d['id'] for d in result.data] or []

def _apply_device_filter(query, device_ids, col='device_id'):
    if device_ids:
        query = query.in_(col, device_ids)
    return query

def _safe_float(val, default=0):
    """Return float, treating None as default."""
    return float(val) if val is not None else default

# ── GET /api/ml-history ───────────────────────────────────────────────────────

@ml_history_bp.route('', methods=['GET'])
@token_required
def get_ml_history():
    """Get combined ML predictions and detections for current user's devices."""
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

        if device_ids == []:          # user has no devices
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
                confidence = 0

                if pt == 'anomaly':
                    health = _safe_float(item.get('device_health_score'))
                    result = {
                        'score':              item.get('anomaly_score'),
                        'severity':           item.get('anomaly_severity'),
                        'device_health_score': health,
                        'message':            f"Device anomaly detected (health: {health:.1f}%)",
                    }
                    confidence = _safe_float(item.get('anomaly_score'))

                elif pt == 'object_detection':
                    obj  = item.get('object_detected', 'object')
                    dist = item.get('distance_cm', 0)
                    result = {
                        'object':        obj, 'obstacle_type': obj,
                        'distance':      dist, 'distance_cm':   dist,
                        'danger_level':  item.get('danger_level'),
                        'confidence':    item.get('detection_confidence'),
                    }
                    confidence = _safe_float(item.get('detection_confidence'))

                elif pt == 'danger_prediction':
                    score  = _safe_float(item.get('danger_score'))
                    action = item.get('recommended_action', 'UNKNOWN')
                    result = {
                        'danger_score':       score,
                        'recommended_action': action,
                        'time_to_collision':  item.get('time_to_collision'),
                        'message':            f"{action} - Danger score: {score:.1f}",
                    }
                    confidence = score / 100

                elif pt == 'environment_classification':
                    env  = item.get('environment_type', 'unknown')
                    light = item.get('lighting_condition', 'unknown')
                    result = {
                        'environment_type': env,
                        'lighting_condition': light,
                        'complexity_level': item.get('complexity_level'),
                        'message': f"{env} - {light} lighting",
                    }
                    confidence = 0.85

                combined.append({
                    'id':               item['id'],
                    'device_id':        item['device_id'],
                    'device_name':      (item.get('user_devices') or {}).get('device_name', 'Unknown'),
                    'prediction_type':  pt,
                    'is_anomaly':       item.get('is_anomaly', False),
                    'confidence_score': confidence,
                    'timestamp':        item['created_at'],
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
                    'confidence_score': 0.85,
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

        # ── real totals (count-only queries) ──────────────────────────────────
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
    """Get anomalies from both tables."""
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user['role']
        limit     = request.args.get('limit', 20, type=int)

        supabase   = get_supabase()
        device_ids = _get_device_ids(supabase, user_id, user_role)

        if device_ids == []:
            return jsonify({'data': []}), 200

        combined = []

        # ── ml_predictions anomalies ──────────────────────────────────────────
        q = supabase.table('ml_predictions')\
            .select('*, user_devices(device_name)')\
            .eq('is_anomaly', True)\
            .order('created_at', desc=True)\
            .limit(limit)
        q = _apply_device_filter(q, device_ids)

        for item in q.execute().data:
            pt       = item.get('prediction_type', 'unknown')
            score    = 0
            severity = 'medium'
            message  = 'Anomaly detected'

            if pt == 'anomaly':
                health   = _safe_float(item.get('device_health_score'))
                score    = _safe_float(item.get('anomaly_score'))
                severity = item.get('anomaly_severity', 'medium')
                message  = f"Device anomaly detected (health: {health:.1f}%)"

            elif pt == 'danger_prediction':
                score    = _safe_float(item.get('danger_score')) / 100
                action   = item.get('recommended_action', 'UNKNOWN')
                severity = 'high' if score > 0.7 else 'medium'
                message  = f"Danger detected - {action} recommended"

            elif pt == 'object_detection':
                score    = _safe_float(item.get('detection_confidence'))
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
                'timestamp':   item['created_at'],
                'source':      'ml_prediction',
            })

        # ── detection_logs anomalies (High danger only) ───────────────────────
        q = supabase.table('detection_logs')\
            .select('*, user_devices(device_name)')\
            .eq('danger_level', 'High')\
            .order('detected_at', desc=True)\
            .limit(limit)
        q = _apply_device_filter(q, device_ids)

        for item in q.execute().data:
            combined.append({
                'id':          item['id'],
                'device_id':   item['device_id'],
                'device_name': (item.get('user_devices') or {}).get('device_name', 'Unknown'),
                'type':        'detection',
                'severity':    item['danger_level'].lower(),
                'message':     f"{item['obstacle_type']} detected at {item['distance_cm']}cm",
                'score':       0.75,
                'timestamp':   item['detected_at'],
                'source':      'detection_log',
            })

        combined.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'data': combined[:limit]}), 200

    except Exception as e:
        print(f"Get anomalies error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get anomalies'}), 500


# ── GET /api/ml-history/stats ─────────────────────────────────────────────────

@ml_history_bp.route('/stats', methods=['GET'])
@token_required
def get_ml_stats():
    """Get combined statistics from both tables."""
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
        print(f"📊 Stats requested for {days} days | {start_iso} → {end_dt.isoformat()}")

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

        total      = ml_total + det_total
        anomalies  = ml_anomalies + det_anomalies
        anom_rate  = (anomalies / total * 100) if total > 0 else 0

        print(f"   ML total: {ml_total} | ML anomalies: {ml_anomalies}")
        print(f"   Det total: {det_total} | Det anomalies: {det_anomalies}")
        print(f"   Combined anomalyCount: {anomalies}")

        by_type = {
            'anomaly':                  ml_count({'prediction_type': 'anomaly'}),
            'object_detection':         ml_count({'prediction_type': 'object_detection'}),
            'danger_prediction':        ml_count({'prediction_type': 'danger_prediction'}),
            'environment_classification': ml_count({'prediction_type': 'environment_classification'}),
            'detection':                det_total,
        }

        # ── avg confidence (fetch scores in one query) ─────────────────────
        conf_scores = []
        try:
            q = supabase.table('ml_predictions')\
                .select('prediction_type, anomaly_score, detection_confidence, danger_score')\
                .gte('created_at', start_iso)
            q = _apply_device_filter(q, device_ids)
            for pred in q.execute().data:
                pt = pred.get('prediction_type')
                if   pt == 'anomaly'            and pred.get('anomaly_score'):
                    conf_scores.append(pred['anomaly_score'])
                elif pt == 'object_detection'   and pred.get('detection_confidence'):
                    conf_scores.append(pred['detection_confidence'])
                elif pt == 'danger_prediction'  and pred.get('danger_score'):
                    conf_scores.append(pred['danger_score'] / 100)
        except Exception as ce:
            print(f"⚠️ Confidence fetch error (non-critical): {ce}")

        if det_total > 0:
            conf_scores.extend([0.85] * det_total)

        avg_conf = (sum(conf_scores) / len(conf_scores)) if conf_scores else 0.75

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
    """
    Return per-day aggregated counts.
    Uses 2 bulk fetches instead of N×8 per-day queries — safe for 90-day range.
    """
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

        end_dt   = now_ph()
        start_dt = end_dt - timedelta(days=days)
        start_iso = start_dt.isoformat()
        end_iso   = end_dt.isoformat()

        # ── BULK FETCH 1: ml_predictions (paginated) ─────────────────────────────
        ml_rows = []
        page = 0
        while True:
            q = supabase.table('ml_predictions')\
                .select('created_at, prediction_type, is_anomaly')\
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

        # ── BULK FETCH 2: detection_logs (paginated) ─────────────────────────────
        det_rows = []
        page = 0
        while True:
            q = supabase.table('detection_logs')\
                .select('detected_at, danger_level')\
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

        # ── Aggregate in Python ──────────────────────────────────────────────
        daily = defaultdict(lambda: defaultdict(int))

        for row in ml_rows:
            day = row['created_at'][:10]
            pt  = row.get('prediction_type', '')
            daily[day][pt]           += 1
            daily[day]['ml_total']   += 1
            if row.get('is_anomaly'):
                daily[day]['ml_anomaly'] += 1

        for row in det_rows:
            day = row['detected_at'][:10]
            daily[day]['det_total'] += 1
            if row.get('danger_level') == 'High':
                daily[day]['det_anomaly'] += 1

        # ── Build result list ────────────────────────────────────────────────
        result = []
        for i in range(days):
            day_dt  = start_dt + timedelta(days=i)
            day_key = day_dt.strftime('%Y-%m-%d')
            d       = daily[day_key]

            count_obj    = d['object_detection']
            count_danger = d['danger_prediction']
            count_anom   = d['anomaly']
            count_env    = d['environment_classification']
            count_det    = d['det_total']
            total        = d['ml_total'] + count_det
            anomalies    = d['ml_anomaly'] + d['det_anomaly']

            avg_confidence = round(
                (count_obj * 0.85 + count_danger * 0.80 +
                 count_anom * 0.85 + count_env * 0.85 +
                 count_det * 0.85) / total * 100, 2
            ) if total > 0 else 0.0

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