"""
ML Data Simulator — inserts directly into Supabase ml_predictions table.
Bypasses the Flask API entirely, so no routing/auth issues.

Usage:
    pip install supabase
    python simulate_ml_data.py \
        --url  https://your-project.supabase.co \
        --key  your-service-role-key \
        --device baeb2051-b987-4b68-aa3b-1caa41c23a50

Find credentials at: Supabase → Project Settings → API
  - Project URL    → --url
  - service_role key → --key  (NOT the anon key — needs RLS bypass)
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone

try:
    from supabase import create_client
except ImportError:
    print("❌ Missing dependency. Run:  pip install supabase")
    sys.exit(1)

# ── How many rows per type ─────────────────────────────────────────────────────
COUNTS = {
    "object_detection":           25,
    "danger_prediction":          25,
    "anomaly":                    20,
    "environment_classification": 20,
}

# ── Spread rows across the last 7 days ────────────────────────────────────────
def random_ts(days_back=7):
    now    = datetime.now(timezone.utc)
    offset = timedelta(seconds=random.randint(0, days_back * 86400))
    return (now - offset).isoformat()


# ── Row builders ───────────────────────────────────────────────────────────────

def make_object_detection(device_id):
    obj_types = ["person","chair","table","door","wall","stairs","car","bicycle","pole","box"]
    obj       = random.choice(obj_types)
    dist      = round(random.uniform(20, 400), 1)
    conf      = round(random.uniform(0.70, 0.98), 3)
    danger    = "High" if dist < 60 else ("Medium" if dist < 120 else "Low")
    return {
        "device_id":            device_id,
        "prediction_type":      "object_detection",
        "object_detected":      obj,
        "distance_cm":          dist,
        "detection_confidence": conf,
        "danger_level":         danger,
        "is_anomaly":           danger == "High",
        "anomaly_severity":     "high" if danger == "High" else ("medium" if danger == "Medium" else "low"),
        "model_source":         "simulator",
        "created_at":           random_ts(),
    }


def make_danger_prediction(device_id):
    dist   = round(random.uniform(10, 350), 1)
    score  = round(max(0, min(100, (1 - dist / 350) * 100 + random.uniform(-10, 10))), 1)
    action = "STOP" if score >= 80 else ("SLOW_DOWN" if score >= 60 else ("CAUTION" if score >= 30 else "SAFE"))
    ttc    = round(dist / max(0.5, random.uniform(0.3, 2.0)), 1) if score > 30 else None
    conf   = round(random.uniform(0.65, 0.97), 3)
    return {
        "device_id":            device_id,
        "prediction_type":      "danger_prediction",
        "danger_score":         score,
        "recommended_action":   action,
        "time_to_collision":    ttc,
        "distance_cm":          dist,
        "detection_confidence": conf,
        "is_anomaly":           score > 70,
        "anomaly_severity":     "high" if score > 70 else ("medium" if score > 40 else "low"),
        "model_source":         "simulator",
        "created_at":           random_ts(),
    }


def make_anomaly(device_id):
    is_anomaly  = random.random() < 0.30
    score       = round(random.uniform(0.55, 0.95), 3) if is_anomaly else round(random.uniform(0.02, 0.25), 3)
    severity    = random.choice(["medium", "high"]) if is_anomaly else "low"
    health      = round(random.uniform(40, 75), 1)     if is_anomaly else round(random.uniform(80, 100), 1)
    needs_maint = is_anomaly and random.random() < 0.4
    return {
        "device_id":              device_id,
        "prediction_type":        "anomaly",
        "is_anomaly":             is_anomaly,
        "anomaly_score":          score,
        "anomaly_severity":       severity,
        "device_health_score":    health,
        "needs_maintenance":      needs_maint,
        "maintenance_priority":   random.choice(["low","medium","high"]) if needs_maint else None,
        "days_until_maintenance": random.randint(1, 14) if needs_maint else None,
        "model_source":           "simulator",
        "created_at":             random_ts(),
    }


def make_environment(device_id):
    scenarios = [
        ("indoor",          "bright", "moderate"),
        ("indoor",          "dim",    "simple"),
        ("outdoor",         "bright", "simple"),
        ("outdoor",         "dim",    "moderate"),
        ("crowded",         "bright", "complex"),
        ("crowded",         "dim",    "complex"),
        ("narrow_corridor", "dim",    "moderate"),
        ("narrow_corridor", "dark",   "complex"),
        ("open_space",      "bright", "simple"),
        ("open_space",      "dim",    "simple"),
    ]
    env_type, lighting, complexity = random.choice(scenarios)
    return {
        "device_id":            device_id,
        "prediction_type":      "environment_classification",
        "environment_type":     env_type,
        "lighting_condition":   lighting,
        "complexity_level":     complexity,
        "detection_confidence": round(random.uniform(0.68, 0.97), 3),
        "is_anomaly":           False,
        "model_source":         "simulator",
        "created_at":           random_ts(),
    }


# ── Insertion helper ───────────────────────────────────────────────────────────

def insert_batch(supabase, rows, label):
    print(f"\n  Inserting {len(rows)} {label} rows...", end="", flush=True)
    try:
        supabase.table("ml_predictions").insert(rows).execute()
        print("  ✓ done")
        return len(rows), 0
    except Exception as e:
        print(f"\n  ⚠ Bulk insert failed ({e}), trying one-by-one...")
        ok = fail = 0
        for row in rows:
            try:
                supabase.table("ml_predictions").insert(row).execute()
                ok += 1
            except Exception as e2:
                fail += 1
                print(f"    ✗ {e2}")
        print(f"  ✓ {ok} ok  ✗ {fail} failed")
        return ok, fail


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Direct Supabase ML data simulator")
    parser.add_argument("--url",    required=True, help="Supabase project URL")
    parser.add_argument("--key",    required=True, help="Supabase service_role key")
    parser.add_argument("--device", required=True, help="Device UUID (user_devices.id)")
    parser.add_argument("--skip",   nargs="*", default=[],
                        choices=["object","danger","anomaly","environment"],
                        help="Types to skip")
    args = parser.parse_args()

    print("=" * 60)
    print("  ML Data Simulator (Direct Supabase)")
    print("=" * 60)
    print(f"  URL    : {args.url}")
    print(f"  Device : {args.device}")
    print(f"  Total  : {sum(COUNTS.values())} rows across 4 ML types")
    print("=" * 60)

    supabase = create_client(args.url, args.key)

    print("\n🔗 Checking Supabase connection...")
    try:
        supabase.table("ml_predictions").select("id", count="exact").limit(1).execute()
        print("   Connected ✓")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("   Check your --url and --key values.")
        sys.exit(1)

    ok_total = fail_total = 0

    def run(label, skip_key, builder, count):
        nonlocal ok_total, fail_total
        if skip_key in (args.skip or []):
            print(f"\n  ⏭  Skipping {label}")
            return
        rows = [builder(args.device) for _ in range(count)]
        ok, fail = insert_batch(supabase, rows, label)
        ok_total   += ok
        fail_total += fail

    run("object_detection",           "object",      make_object_detection, COUNTS["object_detection"])
    run("danger_prediction",          "danger",      make_danger_prediction, COUNTS["danger_prediction"])
    run("anomaly",                    "anomaly",     make_anomaly,           COUNTS["anomaly"])
    run("environment_classification", "environment", make_environment,       COUNTS["environment_classification"])

    print("\n" + "=" * 60)
    print(f"  Done.  ✓ {ok_total} inserted   ✗ {fail_total} failed")
    print("=" * 60)

    if fail_total == 0:
        print("\n✅ Refresh your dashboard — all ML widgets should now show data.")
    else:
        print(f"\n⚠️  {fail_total} rows failed.")
        print("   Make sure you used the service_role key, not the anon key.")


if __name__ == "__main__":
    main()