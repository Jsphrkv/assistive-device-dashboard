from flask import Blueprint, request, jsonify
from app.services.supabase_client import get_supabase
from app.middleware.auth import token_required
from datetime import datetime, timedelta

ml_history_bp = Blueprint('ml_history', __name__, url_prefix='/api/ml-history')

@ml_history_bp.route('', methods=['GET'])
@token_required
def get_ml_history():
    """Get combined ML predictions and detections for current user's devices"""
    try:
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        prediction_type = request.args.get('type')  # anomaly, activity, maintenance, detection
        source = request.args.get('source', 'all')  # 'predictions', 'detections', 'all'
        anomalies_only = request.args.get('anomalies_only', 'false').lower() == 'true'
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        supabase = get_supabase()
        
        # ✅ Get user's device IDs (account scoping)
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
        
        # ✅ Fetch from ml_predictions table
        if source in ['all', 'predictions']:
            ml_query = supabase.table('ml_predictions')\
                .select('*, user_devices(device_name)')
            
            if device_ids:
                ml_query = ml_query.in_('device_id', device_ids)
            
            if prediction_type and prediction_type != 'detection':
                ml_query = ml_query.eq('prediction_type', prediction_type)
            
            if anomalies_only:
                ml_query = ml_query.eq('is_anomaly', True)
            
            if start_date:
                ml_query = ml_query.gte('created_at', start_date)
            
            if end_date:
                ml_query = ml_query.lte('created_at', end_date)
            
            ml_response = ml_query.order('created_at', desc=True).limit(limit).execute()
            
            # Transform ML predictions
            for item in ml_response.data:
                result = {}
                confidence = 0
                
                if item.get('prediction_type') == 'anomaly':
                    result = {
                        'score': item.get('anomaly_score'),
                        'severity': item.get('anomaly_severity'),
                        'message': item.get('anomaly_message')
                    }
                    confidence = item.get('anomaly_score', 0)
                elif item.get('prediction_type') == 'maintenance':
                    result = {
                        'needs_maintenance': item.get('needs_maintenance'),
                        'confidence': item.get('maintenance_confidence'),
                        'priority': item.get('maintenance_priority'),
                        'recommendation': item.get('maintenance_recommendation')
                    }
                    confidence = item.get('maintenance_confidence', 0)
                elif item.get('prediction_type') == 'activity':
                    result = {
                        'activity': item.get('detected_activity'),
                        'confidence': item.get('activity_confidence'),
                        'intensity': item.get('activity_intensity'),
                        'probabilities': item.get('activity_probabilities')
                    }
                    confidence = item.get('activity_confidence', 0)
                
                combined_data.append({
                    'id': item['id'],
                    'device_id': item['device_id'],
                    'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                    'prediction_type': item['prediction_type'],
                    'is_anomaly': item['is_anomaly'],
                    'confidence_score': confidence,
                    'timestamp': item['created_at'],
                    'result': result,
                    'source': 'ml_prediction'
                })
        
        # ✅ Fetch from detection_logs table
        if source in ['all', 'detections'] and prediction_type in [None, 'detection']:
            det_query = supabase.table('detection_logs')\
                .select('*, user_devices!detection_logs_device_id_fkey(device_name)')
            
            if device_ids:
                det_query = det_query.in_('device_id', device_ids)
            
            # Treat High/Critical as anomalies
            if anomalies_only:
                det_query = det_query.in_('danger_level', ['High', 'Critical'])
            
            if start_date:
                det_query = det_query.gte('detected_at', start_date)
            
            if end_date:
                det_query = det_query.lte('detected_at', end_date)
            
            det_response = det_query.order('detected_at', desc=True).limit(limit).execute()
            
            # Transform detections
            for item in det_response.data:
                combined_data.append({
                    'id': item['id'],
                    'device_id': item['device_id'],
                    'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                    'prediction_type': 'detection',
                    'is_anomaly': item['danger_level'] in ['High', 'Critical'],
                    'confidence_score': 0.85,  # Default confidence for detections
                    'timestamp': item['detected_at'],
                    'result': {
                        'obstacle_type': item['obstacle_type'],
                        'distance': item['distance_cm'],
                        'danger_level': item['danger_level'],
                        'alert_type': item.get('alert_type')
                    },
                    'source': 'detection_log'
                })
        
        # ✅ Sort combined data by timestamp
        combined_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # ✅ Apply pagination to combined results
        paginated_data = combined_data[offset:offset + limit]
        
        return jsonify({
            'data': paginated_data,
            'total': len(combined_data),
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
        
        # Get user's devices
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
        
        # ✅ Get ML prediction anomalies
        if device_ids:
            ml_response = supabase.table('ml_predictions')\
                .select('*, user_devices(device_name)')\
                .in_('device_id', device_ids)\
                .eq('is_anomaly', True)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
        else:
            ml_response = supabase.table('ml_predictions')\
                .select('*, user_devices(device_name, users(username))')\
                .eq('is_anomaly', True)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
        
        for item in ml_response.data:
            combined_anomalies.append({
                'id': item['id'],
                'device_id': item['device_id'],
                'device_name': item.get('user_devices', {}).get('device_name', 'Unknown'),
                'type': item['prediction_type'],
                'severity': item.get('anomaly_severity', 'medium'),
                'message': item.get('anomaly_message', 'Anomaly detected'),
                'score': item.get('anomaly_score', 0),
                'timestamp': item['created_at'],
                'source': 'ml_prediction'
            })
        
        # ✅ Get detection log anomalies (High/Critical danger)
        if device_ids:
            det_response = supabase.table('detection_logs')\
                .select('*, user_devices(device_name)')\
                .in_('device_id', device_ids)\
                .in_('danger_level', ['High', 'Critical'])\
                .order('detected_at', desc=True)\
                .limit(limit)\
                .execute()
        else:
            det_response = supabase.table('detection_logs')\
                .select('*, user_devices(device_name, users(username))')\
                .in_('danger_level', ['High', 'Critical'])\
                .order('detected_at', desc=True)\
                .limit(limit)\
                .execute()
        
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
        
        # Sort by timestamp
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
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # ✅ ML predictions stats
        if device_ids:
            ml_total = supabase.table('ml_predictions')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .gte('created_at', start_date.isoformat())\
                .execute()
            
            ml_anomalies = supabase.table('ml_predictions')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .gte('created_at', start_date.isoformat())\
                .eq('is_anomaly', True)\
                .execute()
        else:
            ml_total = supabase.table('ml_predictions')\
                .select('*', count='exact')\
                .gte('created_at', start_date.isoformat())\
                .execute()
            
            ml_anomalies = supabase.table('ml_predictions')\
                .select('*', count='exact')\
                .gte('created_at', start_date.isoformat())\
                .eq('is_anomaly', True)\
                .execute()
        
        # ✅ Detection logs stats
        if device_ids:
            det_total = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .gte('detected_at', start_date.isoformat())\
                .execute()
            
            det_anomalies = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .in_('device_id', device_ids)\
                .gte('detected_at', start_date.isoformat())\
                .in_('danger_level', ['High', 'Critical'])\
                .execute()
        else:
            det_total = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .gte('detected_at', start_date.isoformat())\
                .execute()
            
            det_anomalies = supabase.table('detection_logs')\
                .select('*', count='exact')\
                .gte('detected_at', start_date.isoformat())\
                .in_('danger_level', ['High', 'Critical'])\
                .execute()
        
        # Combined totals
        total_predictions = ml_total.count + det_total.count
        total_anomalies = ml_anomalies.count + det_anomalies.count
        anomaly_rate = (total_anomalies / total_predictions * 100) if total_predictions > 0 else 0
        
        # Count by type
        by_type = {}
        for pred in ml_total.data:
            pred_type = pred.get('prediction_type', 'unknown')
            by_type[pred_type] = by_type.get(pred_type, 0) + 1
        
        by_type['detection'] = det_total.count
        
        # By source
        by_source = {
            'ml_predictions': ml_total.count,
            'detection_logs': det_total.count
        }
        
        # Average confidence
        confidence_scores = []
        for pred in ml_total.data:
            if pred.get('anomaly_score'):
                confidence_scores.append(pred['anomaly_score'])
            elif pred.get('activity_confidence'):
                confidence_scores.append(pred['activity_confidence'])
            elif pred.get('maintenance_confidence'):
                confidence_scores.append(pred['maintenance_confidence'])
        
        avg_confidence = (sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0.75
        
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