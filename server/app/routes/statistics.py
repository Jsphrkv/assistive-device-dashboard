from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required, admin_required, check_permission

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _device_ids(supabase, user_id, user_role):
    """Return device UUID list for user, or None for admin."""
    if user_role == 'admin':
        return None
    result = supabase.table('user_devices').select('id').eq('user_id', user_id).execute()
    ids = [d['id'] for d in result.data]
    return ids if ids else ['no-devices']


def _det_count(supabase, device_ids, filters=None):
    """Count detection_logs rows, optionally filtered."""
    q = supabase.table('detection_logs').select('*', count='exact', head=True)
    if device_ids:
        q = q.in_('device_id', device_ids)
    if filters:
        for col, val in filters.items():
            q = q.in_(col, val) if isinstance(val, list) else q.eq(col, val)
    return q.execute().count or 0


# ── GET /api/statistics/daily/<days> ─────────────────────────────────────────

@statistics_bp.route('/daily/<int:days>', methods=['GET'])
@token_required
def get_daily_stats(days):
    """Get daily statistics for current user."""
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        supabase  = get_supabase()

        print(f"📊 Fetching daily stats for user {user_id} (last {days} days)")

        q = supabase.table('daily_statistics').select('*').order('stat_date', desc=True).limit(days)
        if user_role != 'admin':
            q = q.eq('user_id', user_id)

        rows = q.execute().data
        print(f"📊 Found {len(rows)} daily statistics records")

        result = sorted([
            {
                'stat_date':    row['stat_date'],
                'date':         row['stat_date'],
                'total_alerts': row.get('total_alerts', 0),
                'alerts':       row.get('total_alerts', 0),
                'high':         row.get('high_priority', 0),
                'medium':       row.get('medium_priority', 0),
                'low':          row.get('low_priority', 0),
            }
            for row in rows
        ], key=lambda x: x['date'])

        print(f"✅ Returning {len(result)} days")
        if result:
            print(f"   Sample: {result[0]}")

        return jsonify({'data': result}), 200

    except Exception as e:
        print(f"❌ Get daily stats error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── GET /api/statistics/obstacles ────────────────────────────────────────────

@statistics_bp.route('/obstacles', methods=['GET'])
@token_required
def get_obstacle_statistics():
    """Get obstacle statistics for current user."""
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        supabase  = get_supabase()

        print(f"📊 Fetching obstacle stats for user {user_id}")

        q = supabase.table('obstacle_statistics').select('*').order('total_count', desc=True).limit(10)
        if user_role != 'admin':
            q = q.eq('user_id', user_id)

        rows = q.execute().data
        print(f"📊 Found {len(rows)} obstacle types")

        result = [
            {
                'obstacle_type': row['obstacle_type'],
                'name':          row['obstacle_type'],
                'total_count':   row['total_count'],
                'value':         row['total_count'],
                'count':         row['total_count'],
                'percentage':    row.get('percentage', 0),
            }
            for row in rows
        ]

        print(f"✅ Returning obstacles:")
        for r in result[:3]:
            print(f"   {r['name']}: {r['value']}")

        return jsonify({'data': result}), 200

    except Exception as e:
        print(f"❌ Get obstacle statistics error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get obstacle statistics'}), 500


# ── GET /api/statistics/hourly ────────────────────────────────────────────────

@statistics_bp.route('/hourly', methods=['GET'])
@token_required
def get_hourly_patterns():
    """Get hourly detection patterns (1-hour intervals, 12AM-11PM)."""
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        supabase  = get_supabase()

        print(f"📊 Fetching hourly patterns for user {user_id}")

        q = supabase.table('hourly_patterns').select('*')
        if user_role != 'admin':
            q = q.eq('user_id', user_id)

        rows = q.execute().data
        print(f"📊 Found {len(rows)} hourly records")

        import re
        def parse_hour(hour_str):
            m = re.match(r'(\d+)(AM|PM)', str(hour_str))
            if not m:
                return 0
            h, period = int(m.group(1)), m.group(2)
            if h == 12:
                return 0 if period == 'AM' else 12
            return h if period == 'AM' else h + 12

        result = sorted([
            {
                'hour_range':      row['hour_range'],
                'hour':            row['hour_range'],
                'detection_count': row.get('detection_count', 0),
                'detections':      row.get('detection_count', 0),
                'count':           row.get('detection_count', 0),
            }
            for row in rows
        ], key=lambda x: parse_hour(x['hour']))

        print(f"✅ Returning {len(result)} hourly data points:")
        for r in result[:5]:
            print(f"   {r['hour']}: {r['detections']} detections")

        return jsonify({'data': result}), 200

    except Exception as e:
        print(f"❌ Get hourly patterns error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get hourly patterns'}), 500


# ── GET /api/statistics/summary ──────────────────────────────────────────────

@statistics_bp.route('/summary', methods=['GET'])
@token_required
def get_ml_statistics():
    """Get ML statistics summary for current user."""
    try:
        user_id   = request.current_user['user_id']
        user_role = request.current_user.get('role', 'user')
        supabase  = get_supabase()

        print(f"📊 Fetching summary stats for user {user_id}")

        device_ids = _device_ids(supabase, user_id, user_role)

        if device_ids == ['no-devices']:
            return jsonify({
                'totalPredictions': 0,
                'anomalyCount':     0,
                'anomalyRate':      0,
                # FIX: removed fake 67.5 — return None so frontend shows "N/A"
                'avgAnomalyScore':  None,
                'severityBreakdown':  {'high': 0, 'medium': 0, 'low': 0},
                'categoryBreakdown':  {'critical': 0, 'navigation': 0, 'environmental': 0},
            }), 200

        total    = _det_count(supabase, device_ids)

        # FIX: anomalies and high_count were the same query run twice.
        # anomalyCount = High danger events (keeps existing frontend meaning).
        # high_count   = same value, reused in severityBreakdown.
        high_count  = _det_count(supabase, device_ids, {'danger_level': 'High'})
        med_count   = _det_count(supabase, device_ids, {'danger_level': 'Medium'})
        low_count   = _det_count(supabase, device_ids, {'danger_level': 'Low'})
        crit_cat    = _det_count(supabase, device_ids, {'object_category': 'critical'})
        nav_cat     = _det_count(supabase, device_ids, {'object_category': 'navigation'})
        env_cat     = _det_count(supabase, device_ids, {'object_category': 'environmental'})

        # FIX: anomalies reuses high_count — no duplicate DB query
        anomalies = high_count
        anom_rate = (anomalies / total * 100) if total > 0 else 0
        print(f"✅ Summary: {total} total, {anomalies} anomalies, {anom_rate:.1f}% rate")

        return jsonify({
            'totalPredictions': total,
            'anomalyCount':     anomalies,
            'anomalyRate':      round(anom_rate, 2),
            # FIX: removed hardcoded 67.5 — no real data source for this value.
            # Frontend should show "N/A" when this is None.
            'avgAnomalyScore':  None,
            'severityBreakdown': {
                'high':   high_count,
                'medium': med_count,
                'low':    low_count,
            },
            'categoryBreakdown': {
                'critical':      crit_cat,
                'navigation':    nav_cat,
                'environmental': env_cat,
            },
        }), 200

    except Exception as e:
        print(f"❌ Get ML statistics error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Failed to get ML statistics'}), 500