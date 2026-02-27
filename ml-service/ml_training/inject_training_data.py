"""
inject_training_data.py
=======================
Injects synthetic training data into Supabase for all 4 ML models.

  Table: detection_logs    → danger_predictor, object_detector
  Table: ml_predictions    → anomaly_detector, environment_classifier

Usage:
  python inject_training_data.py               # inject all 4 models (default counts)
  python inject_training_data.py --models danger object      # specific models only
  python inject_training_data.py --count 500                 # 500 rows per model
  python inject_training_data.py --dry-run                   # preview without inserting
  python inject_training_data.py --clear                     # delete injected rows first
"""

import os
import sys
import argparse
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Supabase setup ────────────────────────────────────────────────────────────
def get_supabase():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        sys.exit(1)
    return create_client(url, key)


# ── Helpers ───────────────────────────────────────────────────────────────────
def rand(lo, hi):
    return round(random.uniform(lo, hi), 4)

def rand_ts(days_back=60):
    """Random timestamp within the last N days."""
    offset = random.randint(0, days_back * 24 * 3600)
    return (datetime.utcnow() - timedelta(seconds=offset)).isoformat()

def chunked(lst, size=100):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


# ─────────────────────────────────────────────────────────────────────────────
# 1. DANGER PREDICTOR  →  detection_logs
#    Features used: distance_cm, danger_level
#    Also fills: object_detected, detection_confidence, proximity_value
#    so object_detector benefits from the same rows too.
# ─────────────────────────────────────────────────────────────────────────────

OBJECT_CLASSES = ["obstacle", "person", "vehicle", "wall", "stairs", "door", "pole"]

DANGER_SCENARIOS = [
    # (label, weight, dist_range, roc_range, proximity_range, confidence_range, objects)
    ("SAFE",      0.25, (200, 400), (-2,  10),  (300,  3000),  (0.55, 0.85), ["obstacle", "wall", "pole"]),
    ("CAUTION",   0.30, (80,  200), (-15, -2),  (2000, 8000),  (0.65, 0.92), ["person", "obstacle", "door"]),
    ("SLOW_DOWN", 0.25, (40,  100), (-30, -10), (8000, 15000), (0.72, 0.96), ["person", "vehicle", "stairs"]),
    ("STOP",      0.20, (10,  50),  (-50, -25), (14000,20000), (0.80, 0.99), ["person", "vehicle", "obstacle"]),
]

# Maps our label → what detection_logs actually stores
DANGER_LEVEL_MAP = {
    "SAFE":      "Low",
    "CAUTION":   "Medium",
    "SLOW_DOWN": "High",
    "STOP":      "High",
}

def generate_detection_logs(n=400, device_id="MyDevice-J"):
    """
    Generates rows for detection_logs.
    Used by: danger_predictor (danger_level + distance_cm)
             object_detector  (object_detected + detection_confidence)
    """
    rows = []
    # Build weighted scenario pool
    pool = []
    for scenario in DANGER_SCENARIOS:
        label, weight, *_ = scenario
        pool.extend([scenario] * int(weight * 100))

    for _ in range(n):
        s = random.choice(pool)
        label, _, dist_r, roc_r, prox_r, conf_r, objects = s

        distance   = rand(*dist_r)
        confidence = rand(*conf_r)
        proximity  = rand(*prox_r)
        obj        = random.choice(objects)

        rows.append({
            "device_id":           device_id,
            "obstacle_type":       obj,
            "alert_type":           DANGER_LEVEL_MAP[label],
            "object_detected":     obj,
            "distance_cm":         distance,
            "detection_confidence": confidence,
            "danger_level":        DANGER_LEVEL_MAP[label],
            "proximity_value":     int(proximity),
            "movement_detected":   label in ("CAUTION", "SLOW_DOWN", "STOP"),
            "location_context":    random.choice(["indoor", "outdoor", "corridor"]),
            "lighting_condition":  random.choice(["bright", "dim", "dark"]),
            "detected_at":         rand_ts(),
            "_injected":           True,   # marker so --clear can remove them
        })
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 2. ANOMALY DETECTOR  →  ml_predictions  (prediction_type = 'anomaly')
#    Features: distance_cm, proximity_value, ambient_light,
#              rate_of_change, detection_count
# ─────────────────────────────────────────────────────────────────────────────

ANOMALY_SCENARIOS = [
    # (name, is_anomaly, weight, feature_ranges)
    ("open_space",           False, 0.20, dict(dist=(150,400), prox=(300,2000),   amb=(400,1500), roc=(-8,8),    cnt=(0.2,2))),
    ("corridor",             False, 0.20, dict(dist=(40,150),  prox=(3000,12000), amb=(200,600),  roc=(-15,5),   cnt=(1,5))),
    ("near_wall",            False, 0.15, dict(dist=(20,60),   prox=(10000,19000),amb=(100,500),  roc=(-2,2),    cnt=(0.1,1))),
    ("crowded",              False, 0.15, dict(dist=(30,120),  prox=(5000,15000), amb=(200,700),  roc=(-20,10),  cnt=(5,15))),
    ("outdoor",              False, 0.15, dict(dist=(200,400), prox=(200,1500),   amb=(800,2000), roc=(-5,5),    cnt=(0.1,1.5))),
    ("sensor_malfunction",   True,  0.05, None),   # special generation
    ("sudden_spike",         True,  0.05, None),
    ("stuck_sensor",         True,  0.025,None),
    ("physical_impossible",  True,  0.025,None),
]

def _anomaly_row(scenario_name, is_anomaly):
    if scenario_name == "sensor_malfunction":
        return dict(
            distance_cm     = random.choice([0, 401, 450]),
            proximity_value = random.choice([0, 65535]),
            ambient_light   = rand(0, 50),
            rate_of_change  = rand(-100, 100),
            detection_count = rand(0, 1),
        )
    if scenario_name == "sudden_spike":
        return dict(
            distance_cm     = rand(350, 400),
            proximity_value = rand(100, 500),
            ambient_light   = rand(200, 800),
            rate_of_change  = rand(80, 200),
            detection_count = rand(0, 1),
        )
    if scenario_name == "stuck_sensor":
        base = rand(100, 105)
        return dict(
            distance_cm     = base,
            proximity_value = rand(4990, 5010),
            ambient_light   = rand(390, 410),
            rate_of_change  = rand(-0.1, 0.1),
            detection_count = rand(20, 30),
        )
    if scenario_name == "physical_impossible":
        return dict(
            distance_cm     = rand(10, 20),
            proximity_value = rand(100, 300),   # very close but proximity says far
            ambient_light   = rand(200, 800),
            rate_of_change  = rand(-50, -40),
            detection_count = rand(10, 20),
        )
    return None   # fallback (shouldn't reach)

def generate_anomaly_predictions(n=300, device_id="MyDevice-J"):
    rows = []
    pool = []
    for s in ANOMALY_SCENARIOS:
        name, is_anom, weight, _ = s
        pool.extend([s] * int(weight * 200))

    for _ in range(n):
        name, is_anom, _, feat_ranges = random.choice(pool)

        if feat_ranges:
            features = dict(
                distance_cm     = rand(*feat_ranges['dist']),
                proximity_value = rand(*feat_ranges['prox']),
                ambient_light   = rand(*feat_ranges['amb']),
                rate_of_change  = rand(*feat_ranges['roc']),
                detection_count = rand(*feat_ranges['cnt']),
            )
        else:
            features = _anomaly_row(name, is_anom)

        rows.append({
            "device_id":        device_id,
            "prediction_type":  "anomaly",
            "input_data":       features,
            "prediction_result":{
                "is_anomaly":   is_anom,
                "anomaly_type": name if is_anom else "normal",
                "score":        rand(-0.5, -0.05) if is_anom else rand(0.05, 0.5),
            },
            "created_at":       rand_ts(),
            "_injected":        True,
        })
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 3. ENVIRONMENT CLASSIFIER  →  ml_predictions  (prediction_type = 'environment')
#    Features: ambient_light_avg, ambient_light_variance, detection_frequency,
#              average_obstacle_distance, proximity_pattern_complexity, distance_variance
# ─────────────────────────────────────────────────────────────────────────────

ENV_SCENARIOS = {
    "indoor":          dict(amb_avg=(200,700),   amb_var=(10,80),   freq=(1,6),    avg_dist=(60,250),  complexity=(3,7),  dist_var=(30,120)),
    "outdoor":         dict(amb_avg=(600,2500),  amb_var=(100,600), freq=(0.3,3),  avg_dist=(100,400), complexity=(1,5),  dist_var=(80,300)),
    "crowded":         dict(amb_avg=(150,800),   amb_var=(20,100),  freq=(6,20),   avg_dist=(25,120),  complexity=(7,10), dist_var=(40,150)),
    "open_space":      dict(amb_avg=(500,2000),  amb_var=(60,350),  freq=(0.1,1.5),avg_dist=(200,400), complexity=(1,3),  dist_var=(80,250)),
    "narrow_corridor": dict(amb_avg=(100,450),   amb_var=(5,35),    freq=(2,8),    avg_dist=(30,110),  complexity=(4,8),  dist_var=(15,55)),
}

LIGHTING_MAP   = {(0,400): "dim", (400,900): "bright", (900,9999): "bright"}
COMPLEXITY_MAP = {(0,4): "simple", (4,7): "moderate", (7,10): "complex"}

def _classify_lighting(amb_avg):
    if amb_avg < 400:  return "dim"
    if amb_avg < 900:  return "bright"
    return "bright"

def _classify_complexity(c):
    if c < 4:  return "simple"
    if c < 7:  return "moderate"
    return "complex"

def generate_environment_predictions(n=300, device_id="MyDevice-J"):
    rows = []
    envs = list(ENV_SCENARIOS.keys())
    # Equal distribution across all 5 env types
    per_env = n // len(envs)

    for env_name, ranges in ENV_SCENARIOS.items():
        for _ in range(per_env):
            amb_avg    = rand(*ranges['amb_avg'])
            amb_var    = rand(*ranges['amb_var'])
            freq       = rand(*ranges['freq'])
            avg_dist   = rand(*ranges['avg_dist'])
            complexity = rand(*ranges['complexity'])
            dist_var   = rand(*ranges['dist_var'])

            rows.append({
                "device_id":       device_id,
                "prediction_type": "environment",
                "input_data": {
                    "ambient_light_avg":            amb_avg,
                    "ambient_light_variance":       amb_var,
                    "detection_frequency":          freq,
                    "average_obstacle_distance":    avg_dist,
                    "proximity_pattern_complexity": complexity,
                    "distance_variance":            dist_var,
                },
                "prediction_result": {
                    "environment": env_name,
                    "lighting":    _classify_lighting(amb_avg),
                    "complexity":  _classify_complexity(complexity),
                },
                "created_at":  rand_ts(),
                "_injected":   True,
            })

    random.shuffle(rows)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# INSERT / CLEAR
# ─────────────────────────────────────────────────────────────────────────────

def insert_rows(supabase, table, rows, dry_run=False, label=""):
    if dry_run:
        print(f"  [DRY RUN] Would insert {len(rows)} rows into {table}")
        if rows:
            print(f"  Sample row: {json.dumps(rows[0], indent=2, default=str)}")
        return

    inserted = 0
    for batch in chunked(rows, 100):
        try:
            supabase.table(table).insert(batch).execute()
            inserted += len(batch)
            print(f"  ✓ {table}: inserted {inserted}/{len(rows)} rows", end="\r")
        except Exception as e:
            print(f"\n  ❌ Batch insert failed: {e}")
    print(f"  ✅ {label}: {inserted} rows → {table}          ")


def clear_injected(supabase, dry_run=False):
    print("\n🗑  Clearing previously injected rows...")
    for table in ["detection_logs", "ml_predictions"]:
        try:
            if dry_run:
                print(f"  [DRY RUN] Would delete rows where _injected=true from {table}")
                continue
            result = supabase.table(table).delete().eq("_injected", True).execute()
            print(f"  ✅ Cleared injected rows from {table}")
        except Exception as e:
            print(f"  ⚠ Could not clear {table}: {e} (column may not exist yet — safe to ignore)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Inject ML training data into Supabase")
    parser.add_argument("--models",   nargs="+",
                        choices=["danger", "object", "anomaly", "environment", "all"],
                        default=["all"],
                        help="Which models to inject data for (default: all)")
    parser.add_argument("--count",    type=int, default=400,
                        help="Rows per model (default: 400)")
    parser.add_argument("--device-id",default="baeb2051-b987-4b68-aa3b-1caa41c23a50",
                        help="device_id to use for injected rows")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Preview rows without inserting")
    parser.add_argument("--clear",    action="store_true",
                        help="Delete previously injected rows before inserting")
    args = parser.parse_args()

    models = args.models
    if "all" in models:
        models = ["danger", "object", "anomaly", "environment"]

    print("=" * 60)
    print("ML Training Data Injector")
    print(f"  Models   : {', '.join(models)}")
    print(f"  Rows each: {args.count}")
    print(f"  Device   : {args.device_id}")
    print(f"  Dry run  : {args.dry_run}")
    print("=" * 60)

    supabase = get_supabase()

    if args.clear:
        clear_injected(supabase, args.dry_run)

    # ── detection_logs (danger + object share the same rows) ─────────────────
    if "danger" in models or "object" in models:
        print(f"\n📦 Generating detection_logs rows...")
        print(f"   (used by: danger_predictor + object_detector)")
        rows = generate_detection_logs(args.count, args.device_id)

        # Print distribution preview
        from collections import Counter
        dl_dist = Counter(r["danger_level"] for r in rows)
        obj_dist = Counter(r["object_detected"] for r in rows)
        print(f"   Danger levels : {dict(dl_dist)}")
        print(f"   Objects       : {dict(obj_dist)}")

        insert_rows(supabase, "detection_logs", rows, args.dry_run,
                    label="danger_predictor + object_detector")

    # ── ml_predictions — anomaly ──────────────────────────────────────────────
    if "anomaly" in models:
        print(f"\n📦 Generating anomaly prediction rows...")
        rows = generate_anomaly_predictions(args.count, args.device_id)
        anom_count = sum(1 for r in rows if r["prediction_result"]["is_anomaly"])
        print(f"   Normal  : {len(rows) - anom_count}")
        print(f"   Anomaly : {anom_count}")
        insert_rows(supabase, "ml_predictions", rows, args.dry_run,
                    label="anomaly_detector")

    # ── ml_predictions — environment ──────────────────────────────────────────
    if "environment" in models:
        print(f"\n📦 Generating environment prediction rows...")
        rows = generate_environment_predictions(args.count, args.device_id)
        from collections import Counter
        env_dist = Counter(r["prediction_result"]["environment"] for r in rows)
        print(f"   Env distribution: {dict(env_dist)}")
        insert_rows(supabase, "ml_predictions", rows, args.dry_run,
                    label="environment_classifier")

    print("\n" + "=" * 60)
    print("✅ Injection complete!")
    print()
    print("Next steps:")
    print("  1. Run your training scripts:")
    print("     python ml_training/train_danger_prediction.py")
    print("     python ml_training/train_object_detection.py")
    print()
    print("  For anomaly + environment, first uncomment load_training_data()")
    print("  in train_anomaly.py and train_environment_classifier.py,")
    print("  then run those scripts too.")
    print("=" * 60)


if __name__ == "__main__":
    main()