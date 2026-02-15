# from app.services.supabase_client import get_supabase
# from datetime import datetime

# class MLStorageService:
#     """Service for storing ML predictions to database"""
    
#     @staticmethod
#     def save_anomaly_prediction(device_id, prediction_data):
#         """Save anomaly detection to database"""
#         try:
#             supabase = get_supabase()
            
#             record = {
#                 'device_id': device_id,
#                 'prediction_type': 'anomaly',
#                 'is_anomaly': prediction_data.get('is_anomaly'),
#                 'anomaly_score': prediction_data.get('anomaly_score'),
#                 'anomaly_severity': prediction_data.get('severity'),
#                 'anomaly_message': prediction_data.get('message'),
#                 'telemetry_data': prediction_data.get('telemetry_data'),
#                 'created_at': datetime.utcnow().isoformat()
#             }
            
#             supabase.table('ml_predictions').insert(record).execute()
#             return True
#         except Exception as e:
#             print(f"Error saving anomaly prediction: {e}")
#             return False
    
#     @staticmethod
#     def save_maintenance_prediction(device_id, prediction_data):
#         """Save maintenance prediction to database"""
#         try:
#             supabase = get_supabase()
            
#             record = {
#                 'device_id': device_id,
#                 'prediction_type': 'maintenance',
#                 'needs_maintenance': prediction_data.get('needs_maintenance'),
#                 'maintenance_confidence': prediction_data.get('confidence'),
#                 'maintenance_priority': prediction_data.get('priority'),
#                 'maintenance_recommendations': prediction_data.get('recommendations'),
#                 'created_at': datetime.utcnow().isoformat()
#             }
            
#             supabase.table('ml_predictions').insert(record).execute()
#             return True
#         except Exception as e:
#             print(f"Error saving maintenance prediction: {e}")
#             return False
    
#     @staticmethod
#     def save_activity_prediction(device_id, prediction_data):
#         """Save activity recognition to database"""
#         try:
#             supabase = get_supabase()
            
#             record = {
#                 'device_id': device_id,
#                 'prediction_type': 'activity',
#                 'detected_activity': prediction_data.get('activity'),
#                 'activity_confidence': prediction_data.get('confidence'),
#                 'activity_intensity': prediction_data.get('intensity'),
#                 'activity_probabilities': prediction_data.get('all_probabilities'),
#                 'sensor_data': prediction_data.get('sensor_data'),
#                 'created_at': datetime.utcnow().isoformat()
#             }
            
#             supabase.table('ml_predictions').insert(record).execute()
#             return True
#         except Exception as e:
#             print(f"Error saving activity prediction: {e}")
#             return False
    
#     @staticmethod
#     def get_ml_history(device_id, prediction_type=None, limit=100):
#         """Retrieve ML prediction history"""
#         try:
#             supabase = get_supabase()
            
#             query = supabase.table('ml_predictions')\
#                 .select('*')\
#                 .eq('device_id', device_id)\
#                 .order('created_at', desc=True)\
#                 .limit(limit)
            
#             if prediction_type:
#                 query = query.eq('prediction_type', prediction_type)
            
#             result = query.execute()
#             return result.data
#         except Exception as e:
#             print(f"Error fetching ML history: {e}")
#             return []

# ml_storage = MLStorageService()