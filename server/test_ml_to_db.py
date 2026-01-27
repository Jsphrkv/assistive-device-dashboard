"""
Test if ML predictions save to database
Run this locally or on Render
"""
import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.services.supabase_client import get_supabase
from app.services.ml_service import ml_service
from datetime import datetime, timezone

def test_ml_predictions():
    print("="*60)
    print("TESTING ML → DATABASE PIPELINE")
    print("="*60)
    
    # Test 1: Check if Supabase connection works
    print("\n[1/4] Testing Supabase connection...")
    try:
        supabase = get_supabase()
        print("✅ Supabase client created")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return
    
    # Test 2: Run anomaly detection
    print("\n[2/4] Running anomaly detection...")
    try:
        result = ml_service.detect_anomaly({
            'temperature': 39.5,
            'heart_rate': 120,
            'battery_level': 15,
            'signal_strength': -85,
            'usage_hours': 20
        })
        print(f"✅ Anomaly prediction result: {result}")
    except Exception as e:
        print(f"❌ Anomaly prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Save to database
    print("\n[3/4] Saving prediction to database...")
    try:
        prediction = {
            'device_id': 'test_manual_insert',
            'prediction_type': 'anomaly',
            'is_anomaly': result.get('is_anomaly', False),
            'anomaly_score': result.get('anomaly_score', 0),
            'anomaly_severity': result.get('severity', 'low'),
            'anomaly_message': result.get('message', ''),
            'telemetry_data': {
                'temperature': 39.5,
                'heart_rate': 120,
                'battery_level': 15,
                'signal_strength': -85,
                'usage_hours': 20
            },
            'model_version': 'v1.0'
        }
        
        print(f"   Attempting to insert: {prediction}")
        
        db_result = supabase.table('ml_predictions').insert(prediction).execute()
        
        if db_result.data:
            print(f"✅ Successfully saved to database!")
            print(f"   Record ID: {db_result.data[0].get('id')}")
            print(f"   Full record: {db_result.data[0]}")
        else:
            print(f"⚠️ Insert returned no data")
            
    except Exception as e:
        print(f"❌ Database save failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Verify data was saved
    print("\n[4/4] Verifying data in database...")
    try:
        check = supabase.table('ml_predictions')\
            .select('*')\
            .eq('device_id', 'test_manual_insert')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if check.data:
            print(f"✅ Data verified in database!")
            print(f"   Found {len(check.data)} record(s)")
            print(f"   Latest record: {check.data[0]}")
        else:
            print(f"❌ No data found in database")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)

if __name__ == "__main__":
    test_ml_predictions()