from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
from datetime import datetime, timedelta
from app.utils.timezone_helper import now_ph, now_ph_iso, PH_TIMEZONE, utc_to_ph

ml_history_bp = Blueprint('ml_history', __name__, url_prefix='/api/ml-history')

@ml_history_bp.route('', methods=['GET'])
@token_required
def get_ml_history():
    """Get combined ML predictions and detections for current user's devices"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        # Get query parameters
        limit = request.args.get('limit', 1000, type=int)
        max_limit = 1000  # Safety cap
        if limit > max_limit:
            limit = max_limit
        offset = request.args.get('offset', 0, type=int)
        prediction_type = request.args.get('type')
        source = request.args.get('source', 'all')
        anomalies_only = request.args.get('anomalies_only', 'false').lower() == 'true'
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        supabase = get_supabase()
        
        # Get user's device IDs (account scoping)
        if user_role == 'admin':
            device_ids = None
        else:
            user_devices = supabase.table('user_devices')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            device_ids = [device['id'] for device in user_devices.data]
            
            if not device_ids:
                return jsonify({
                    'data': [],
                    'total': 0,
                    'limit': limit,
                    'offset': offset
                }), 200
        
        combined_data = []
        
        # Fetch from ml_predictions table
        if source in ['all', 'predictions']:
            ml_query = supabase.table('ml_predictions')\
                .select('*, user_devices(device_name)')
            
            if device_ids:
                ml_query = ml_query.in_('device_id', device_ids)
            
            # Map frontend type names to database names
            if prediction_type:
                type_mapping = {
                    'detection': 'object_detection',
                    'danger': 'danger_prediction',
                    'environment': 'environment_classification',
                    'anomaly': 'anomaly',
                }
                db_type = type_mapping.get(prediction_type, prediction_type)
                ml_query = ml_query.eq('prediction_type', db_type)
            
            if anomalies_only:
                ml_query = ml_query.eq('is_anomaly', True)
            
            if start_date:
                ml_query = ml_query.gte('created_at', start_date)
            
            if end_date:
                ml_query = ml_query.lte('created_at', end_date)
            
            ml_response = ml_query.order('created_at', desc=True).limit(limit).execute()
            
            for item in ml_response.data:
                result = {}
                confidence = 0
                pred_type = item.get('prediction_type', 'unknown')
                
                if pred_type == 'anomaly':
                    result = {
                        'score': item.get('anomaly_score'),
                        'severity': item.get('anomaly_severity'),
                        'device_health_score': item.get('device_health_score'),
                        'message': f"Device anomaly detected (health: {item.get('device_health_score', 0):.1f}%)"
                    }
                    confidence = item.get('anomaly_score', 0)
                    
                elif pred_type == 'object_detection':
                    obj = item.get('object_detected', 'object')
                    distance = item.get('distance_cm', 0)
                    result = {
                        'object': obj,
                        'obstacle_type': obj,
                        'distance': distance,
                        'distance_cm': distance,
                        'danger_level': item.get('danger_level'),
                        'confidence': item.get('detection_confidence')
                    }
                    confidence = item.get('detection_confidence', 0)
                    
                elif pred_type == 'danger_prediction':
                    result = {
                        'danger_score': item.get('danger_score'),
                        'recommended_action': item.get('recommended_action'),
                        'time_to_collision': item.get('time_to_collision'),
                        'message': f"{item.get('recommended_action', 'UNKNOWN')} - Danger score: {item.get('danger_score', 0):.1f}"
                    }
                    confidence = item.get('danger_score', 0) / 100
                    
                elif pred_type == 'environment_classification':
                    result = {
                        'environment_type': item.get('environment_type'),
                        'lighting_condition': item.get('lighting_condition'),
                        'complexity_level': item.get('complexity_level'),
                        'message': f"{item.get('environment_type', 'unknown')} - {item.get('lighting_condition', 'unknown')} lighting"
                    }
                    confidence = 0.85
                
                combined_data.append({
                    'id': item['id'],
                    'device_id': item['device_id'],
                    'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                    'prediction_type': pred_type,
                    'is_anomaly': item.get('is_anomaly', False),
                    'confidence_score': confidence,
                    'timestamp': item['created_at'],
                    'result': result,
                    'source': 'ml_prediction'
                })
        
        # Fetch from detection_logs table
        if source in ['all', 'detections'] and prediction_type in [None, 'detection']:
            det_query = supabase.table('detection_logs')\
                .select('*, user_devices!detection_logs_device_id_fkey(device_name)')
            
            if device_ids:
                det_query = det_query.in_('device_id', device_ids)
            
            if anomalies_only:
                det_query = det_query.in_('danger_level', ['High', 'Critical'])
            
            if start_date:
                det_query = det_query.gte('detected_at', start_date)
            
            if end_date:
                det_query = det_query.lte('detected_at', end_date)
            
            det_response = det_query.order('detected_at', desc=True).limit(limit).execute()
            
            for item in det_response.data:
                combined_data.append({
                    'id': item['id'],
                    'device_id': item['device_id'],
                    'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                    'prediction_type': 'detection',
                    'is_anomaly': item['danger_level'] in ['High', 'Critical'],
                    'confidence_score': 0.85,
                    'timestamp': item['detected_at'],
                    'result': {
                        'obstacle_type': item['obstacle_type'],
                        'distance': item['distance_cm'],
                        'distance_cm': item['distance_cm'],
                        'danger_level': item['danger_level'],
                        'alert_type': item.get('alert_type')
                    },
                    'source': 'detection_log'
                })
        
        # Sort combined data by timestamp
        combined_data.sort(key=lambda x: x['timestamp'], reverse=True)

        # Get real total counts using count='exact' with head=True
        real_total = 0
        try:
            if source in ['all', 'predictions']:
                ml_count_query = supabase.table('ml_predictions')\
                    .select('*', count='exact', head=True)
                if device_ids:
                    ml_count_query = ml_count_query.in_('device_id', device_ids)
                if anomalies_only:
                    ml_count_query = ml_count_query.eq('is_anomaly', True)
                ml_count_result = ml_count_query.execute()
                real_total += ml_count_result.count or 0

            if source in ['all', 'detections'] and prediction_type in [None, 'detection']:
                det_count_query = supabase.table('detection_logs')\
                    .select('*', count='exact', head=True)
                if device_ids:
                    det_count_query = det_count_query.in_('device_id', device_ids)
                if anomalies_only:
                    det_count_query = det_count_query.in_('danger_level', ['High', 'Critical'])
                det_count_result = det_count_query.execute()
                real_total += det_count_result.count or 0
        except Exception as e:
            print(f"⚠️ Total count error: {e}")
            real_total = len(combined_data)
        
        # Apply pagination to combined results
        paginated_data = combined_data[offset:offset + limit]
        
        return jsonify({
            'data': paginated_data,
            'total': real_total,
            'fetched': len(combined_data),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Get ML history error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get ML history'}), 500


@ml_history_bp.route('/anomalies', methods=['GET'])
@token_required
def get_anomalies():
    """Get anomalies from both tables"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        limit = request.args.get('limit', 20, type=int)
        
        supabase = get_supabase()
        
        if user_role != 'admin':
            user_devices = supabase.table('user_devices')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            device_ids = [device['id'] for device in user_devices.data]
            
            if not device_ids:
                return jsonify({'data': []}), 200
        else:
            device_ids = None
        
        combined_anomalies = []
        
        # Get ML prediction anomalies
        ml_query = supabase.table('ml_predictions')\
            .select('*, user_devices(device_name)')\
            .eq('is_anomaly', True)\
            .order('created_at', desc=True)\
            .limit(limit)
        
        if device_ids:
            ml_query = ml_query.in_('device_id', device_ids)
        
        ml_response = ml_query.execute()
        
        for item in ml_response.data:
            pred_type = item.get('prediction_type', 'unknown')
            score = 0
            message = 'Anomaly detected'
            severity = 'medium'
            
            if pred_type == 'anomaly':
                score = item.get('anomaly_score', 0)
                severity = item.get('anomaly_severity', 'medium')
                message = f"Device anomaly detected (health: {item.get('device_health_score', 0):.1f}%)"
                
            elif pred_type == 'danger_prediction':
                score = item.get('danger_score', 0) / 100
                action = item.get('recommended_action', 'UNKNOWN')
                severity = 'high' if score > 0.7 else 'medium'
                message = f"Danger detected - {action} recommended"
                
            elif pred_type == 'object_detection':
                score = item.get('detection_confidence', 0)
                danger = item.get('danger_level', 'low')
                severity = danger.lower()
                obj = item.get('object_detected', 'object')
                distance = item.get('distance_cm', 0)
                message = f"{obj.capitalize()} detected at {distance}cm"
            
            combined_anomalies.append({
                'id': item['id'],
                'device_id': item['device_id'],
                'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                'type': pred_type,
                'severity': severity,
                'message': message,
                'score': score,
                'timestamp': item['created_at'],
                'source': 'ml_prediction'
            })
        
        # Get detection log anomalies (High/Critical danger)
        det_query = supabase.table('detection_logs')\
            .select('*, user_devices(device_name)')\
            .in_('danger_level', ['High', 'Critical'])\
            .order('detected_at', desc=True)\
            .limit(limit)
        
        if device_ids:
            det_query = det_query.in_('device_id', device_ids)
        
        det_response = det_query.execute()
        
        for item in det_response.data:
            combined_anomalies.append({
                'id': item['id'],
                'device_id': item['device_id'],
                'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                'type': 'detection',
                'severity': item['danger_level'].lower(),
                'message': f"{item['obstacle_type']} detected at {item['distance_cm']}cm",
                'score': 0.9 if item['danger_level'] == 'Critical' else 0.75,
                'timestamp': item['detected_at'],
                'source': 'detection_log'
            })
        
        combined_anomalies.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'data': combined_anomalies[:limit]}), 200
        
    except Exception as e:
        print(f"Get anomalies error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get anomalies'}), 500


@ml_history_bp.route('/stats', methods=['GET'])
@token_required
def get_ml_stats():
    """Get combined statistics from both tables"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        days = request.args.get('days', 7, type=int)
        
        supabase = get_supabase()
        
        # Get user's devices
        if user_role != 'admin':
            user_devices = supabase.table('user_devices')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            device_ids = [device['id'] for device in user_devices.data]
            
            if not device_ids:
                return jsonify({
                    'totalPredictions': 0,
                    'anomalyCount': 0,
                    'anomalyRate': 0,
                    'avgConfidence': 0,
                    'byType': {},
                    'bySource': {}
                }), 200
        else:
            device_ids = None
        
        # ✅ FIXED: Use Philippine time for date range
        end_date = now_ph()
        start_date = end_date - timedelta(days=days)
        start_iso = start_date.isoformat()

        print(f"📊 Stats requested for {days} days | {start_iso} → {end_date.isoformat()}")

        # ─── Helper: build a base count query ───────────────────────────────
        def ml_base(extra_filters=None):
            q = supabase.table('ml_predictions')\
                .select('*', count='exact', head=True)\
                .gte('created_at', start_iso)
            if device_ids:
                q = q.in_('device_id', device_ids)
            if extra_filters:
                for col, val in extra_filters.items():
                    if isinstance(val, list):
                        q = q.in_(col, val)
                    else:
                        q = q.eq(col, val)
            return q

        def det_base(extra_filters=None):
            q = supabase.table('detection_logs')\
                .select('*', count='exact', head=True)\
                .gte('detected_at', start_iso)
            if device_ids:
                q = q.in_('device_id', device_ids)
            if extra_filters:
                for col, val in extra_filters.items():
                    if isinstance(val, list):
                        q = q.in_(col, val)
                    else:
                        q = q.eq(col, val)
            return q

        # ─── Total counts ────────────────────────────────────────────────────
        ml_total_count   = ml_base().execute().count or 0
        det_total_count  = det_base().execute().count or 0

        # ─── Anomaly counts ──────────────────────────────────────────────────
        ml_anomaly_count  = ml_base({'is_anomaly': True}).execute().count or 0
        det_anomaly_count = det_base({'danger_level': ['High', 'Critical']}).execute().count or 0

        total_predictions = ml_total_count + det_total_count
        total_anomalies   = ml_anomaly_count + det_anomaly_count
        anomaly_rate      = (total_anomalies / total_predictions * 100) if total_predictions > 0 else 0

        print(f"   ML total: {ml_total_count} | ML anomalies: {ml_anomaly_count}")
        print(f"   Det total: {det_total_count} | Det anomalies: {det_anomaly_count}")
        print(f"   Combined anomalyCount: {total_anomalies}")

        # ─── Per-type counts ─────────────────────────────────────────────────
        type_anomaly     = ml_base({'prediction_type': 'anomaly'}).execute().count or 0
        type_obj_detect  = ml_base({'prediction_type': 'object_detection'}).execute().count or 0
        type_danger      = ml_base({'prediction_type': 'danger_prediction'}).execute().count or 0
        type_environment = ml_base({'prediction_type': 'environment_classification'}).execute().count or 0

        by_type = {
            'anomaly': type_anomaly,
            'object_detection': type_obj_detect,
            'danger_prediction': type_danger,
            'environment_classification': type_environment,
            'detection': det_total_count,
        }

        by_source = {
            'ml_predictions': ml_total_count,
            'detection_logs': det_total_count
        }

        # ─── Average confidence ───────────────────────────────────────────────
        conf_scores = []
        try:
            conf_query = supabase.table('ml_predictions')\
                .select('prediction_type, anomaly_score, detection_confidence, danger_score')\
                .gte('created_at', start_iso)
            if device_ids:
                conf_query = conf_query.in_('device_id', device_ids)

            conf_response = conf_query.execute()

            for pred in conf_response.data:
                pt = pred.get('prediction_type')
                if pt == 'anomaly' and pred.get('anomaly_score'):
                    conf_scores.append(pred['anomaly_score'])
                elif pt == 'object_detection' and pred.get('detection_confidence'):
                    conf_scores.append(pred['detection_confidence'])
                elif pt == 'danger_prediction' and pred.get('danger_score'):
                    conf_scores.append(pred['danger_score'] / 100)
        except Exception as ce:
            print(f"⚠️ Confidence fetch error (non-critical): {ce}")

        # Detection logs use default 0.85 confidence
        if det_total_count > 0:
            conf_scores.extend([0.85] * det_total_count)

        avg_confidence = (sum(conf_scores) / len(conf_scores)) if conf_scores else 0.75

        return jsonify({
            'totalPredictions': total_predictions,
            'anomalyCount': total_anomalies,
            'anomalyRate': round(anomaly_rate, 2),
            'avgConfidence': round(avg_confidence * 100, 2),
            'byType': by_type,
            'bySource': by_source
        }), 200
        
    except Exception as e:
        print(f"Get ML stats error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get ML stats'}), 500

    
@ml_history_bp.route('/daily-summary', methods=['GET'])
@token_required
def get_daily_summary():
    """
    Return per-day aggregated counts using COUNT queries only.
    Zero row data transferred — always matches stats cards exactly.
    """
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        days = request.args.get('days', 7, type=int)

        if days not in (7, 30, 90):
            days = 7

        supabase = get_supabase()

        # ── Scope to user's devices ──────────────────────────────────────────
        if user_role == 'admin':
            device_ids = None
        else:
            user_devices = supabase.table('user_devices') \
                .select('id') \
                .eq('user_id', user_id) \
                .execute()
            device_ids = [d['id'] for d in user_devices.data]

            if not device_ids:
                return jsonify({'data': []}), 200

        # ✅ FIXED: Philippine time date range
        end_dt = now_ph()
        start_dt = end_dt - timedelta(days=days)

        # ── Helper: COUNT query builders (no rows, just metadata) ────────────
        def ml_count(day_start, day_end, extra_filters=None):
            q = supabase.table('ml_predictions') \
                .select('*', count='exact', head=True) \
                .gte('created_at', day_start) \
                .lt('created_at', day_end)
            if device_ids:
                q = q.in_('device_id', device_ids)
            if extra_filters:
                for col, val in extra_filters.items():
                    if isinstance(val, list):
                        q = q.in_(col, val)
                    else:
                        q = q.eq(col, val)
            return q.execute().count or 0

        def det_count(day_start, day_end, extra_filters=None):
            q = supabase.table('detection_logs') \
                .select('*', count='exact', head=True) \
                .gte('detected_at', day_start) \
                .lt('detected_at', day_end)
            if device_ids:
                q = q.in_('device_id', device_ids)
            if extra_filters:
                for col, val in extra_filters.items():
                    if isinstance(val, list):
                        q = q.in_(col, val)
                    else:
                        q = q.eq(col, val)
            return q.execute().count or 0

        # ── Build result day by day ──────────────────────────────────────────
        result = []

        for i in range(days):
            day_dt    = start_dt + timedelta(days=i)
            next_dt   = day_dt + timedelta(days=1)
            day_start = day_dt.isoformat()
            day_end   = next_dt.isoformat()
            day_key   = day_dt.strftime('%Y-%m-%d')
            day_label = day_dt.strftime('%b %-d')  # e.g. "Feb 13"

            # ── Per-type counts from ml_predictions ─────────────────────────
            count_anomaly_type = ml_count(day_start, day_end, {'prediction_type': 'anomaly'})
            count_obj_detect   = ml_count(day_start, day_end, {'prediction_type': 'object_detection'})
            count_danger       = ml_count(day_start, day_end, {'prediction_type': 'danger_prediction'})
            count_environment  = ml_count(day_start, day_end, {'prediction_type': 'environment_classification'})

            # ── Detection logs count ─────────────────────────────────────────
            count_det_logs     = det_count(day_start, day_end)

            # ── Anomaly counts (ml is_anomaly flag + High/Critical det logs) ─
            ml_anomaly_count   = ml_count(day_start, day_end, {'is_anomaly': True})
            det_anomaly_count  = det_count(day_start, day_end, {'danger_level': ['High', 'Critical']})
            total_anomalies    = ml_anomaly_count + det_anomaly_count

            # ── Totals ───────────────────────────────────────────────────────
            ml_total = count_anomaly_type + count_obj_detect + count_danger + count_environment
            total    = ml_total + count_det_logs

            # ── Avg confidence (weighted estimate, no row fetch needed) ──────
            conf_sum = 0.0
            if total > 0:
                conf_sum += count_obj_detect   * 0.85
                conf_sum += count_danger       * 0.80
                conf_sum += count_anomaly_type * 0.85
                conf_sum += count_environment  * 0.85
                conf_sum += count_det_logs     * 0.85
                avg_confidence = round((conf_sum / total) * 100, 2)
            else:
                avg_confidence = 0.0

            result.append({
                'date_iso':           day_key,
                'date':               day_label,
                'anomalies':          total_anomalies,
                # detections = object_detection ML rows + all detection_log rows
                'detections':         count_obj_detect + count_det_logs,
                'danger_predictions': count_danger,
                'avg_confidence':     avg_confidence,
                'total_logs':         total,
            })

        return jsonify({'data': result}), 200

    except Exception as e:
        print(f"Get daily summary error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get daily summary'}), 500