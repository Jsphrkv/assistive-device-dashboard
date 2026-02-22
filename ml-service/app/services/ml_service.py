import numpy as np
from ml_models.model_loader import load_model


def _load_bundle(name):
    """Load model bundle and return (model, scaler) tuple."""
    bundle = load_model(name)
    if bundle and isinstance(bundle, dict):
        return bundle.get('model'), bundle.get('scaler')
    return bundle, None   # fallback: bundle is the model itself


def _clamp(value, lo, hi, name='value'):
    """Clamp a numeric value to [lo, hi] with a warning if out of range."""
    if value < lo or value > hi:
        print(f"[MLService] ⚠️  {name}={value} out of expected [{lo}, {hi}], clamping")
    return max(lo, min(hi, value))


class MLService:

    # ── Object Detection ──────────────────────────────────────────────────────

    def detect_object(self, data):
        """
        Predict what object type is present given sensor readings.

        Changes from original:
          - Feature validation / clamping before model inference
          - model_source tracked ('ml_model' vs 'fallback') for monitoring
          - Graceful handling of scaler mismatch errors
        """
        # Validate + clamp inputs
        distance  = _clamp(float(data.get('distance_cm',          0)),    0, 1000, 'distance_cm')
        conf      = _clamp(float(data.get('detection_confidence', 0.65)), 0, 1.0,  'detection_confidence')
        proximity = _clamp(float(data.get('proximity_value',      0)),    0, 65535, 'proximity_value')
        light     = _clamp(float(data.get('ambient_light',        0)),    0, 10000, 'ambient_light')

        model, scaler = _load_bundle('object_detector')
        model_source  = 'fallback'

        if model:
            try:
                features = np.array([[distance, conf, proximity, light]])
                if scaler:
                    features = scaler.transform(features)
                object_detected = str(model.predict(features)[0])
                model_source    = 'ml_model'
            except Exception as e:
                print(f"[MLService] Object model error: {e}")
                object_detected = self._object_by_distance(distance)
        else:
            object_detected = self._object_by_distance(distance)

        danger = self._distance_to_danger(distance)
        return {
            'object_detected':      object_detected,
            'distance_cm':          distance,
            'danger_level':         danger,
            'detection_confidence': conf,
            'model_source':         model_source,
            'message': f"{object_detected} at {distance:.0f}cm - {danger} danger"
        }

    def _object_by_distance(self, d):
        if d < 50:  return 'obstacle_close'
        if d < 150: return 'obstacle'
        if d < 300: return 'obstacle_far'
        return 'clear'

    def _distance_to_danger(self, d):
        if d < 30:  return 'Critical'
        if d < 100: return 'High'
        if d < 200: return 'Medium'
        return 'Low'

    # ── Danger Prediction ─────────────────────────────────────────────────────

    def predict_danger(self, data):
        """
        Predict danger score (0–100) and recommended action.

        Changes from original:
          - Feature validation / clamping
          - object_type risk multiplier: persons and vehicles escalate danger sooner
          - Time-to-collision uses speed estimate when roc is unavailable
          - model_source tracked
        """
        distance  = _clamp(float(data.get('distance_cm',           200)), 0,   1000, 'distance_cm')
        roc       = float(data.get('rate_of_change',   0))   # cm/s, negative = approaching
        speed     = _clamp(float(data.get('current_speed_estimate', 1.0)), 0,    10, 'current_speed_estimate')
        proximity = _clamp(float(data.get('proximity_value',          0)), 0, 65535, 'proximity_value')
        obj_type  = data.get('object_type', 'obstacle')

        # Object-type risk multiplier — higher means danger triggers at greater distance
        _risk = {
            'person':   1.5,
            'vehicle':  1.4,
            'stairs':   1.3,
            'animal':   1.2,
            'door':     1.0,
            'obstacle': 1.0,
        }
        risk_mult = _risk.get(obj_type, 1.0)

        model, scaler = _load_bundle('danger_predictor')
        model_source  = 'fallback'

        if model:
            try:
                # 4 features only — matches the existing trained scaler.
                # risk_mult is applied post-inference so no retraining needed.
                features = np.array([[distance, roc, proximity, speed]])
                if scaler:
                    features = scaler.transform(features)
                score        = float(model.predict(features)[0])
                score       *= risk_mult   # boost score for high-risk object types
                model_source = 'ml_model'
            except Exception as e:
                print(f"[MLService] Danger model error: {e}")
                score = self._danger_score(distance, roc, risk_mult)
        else:
            score = self._danger_score(distance, roc, risk_mult)

        score = max(0.0, min(100.0, score))

        # Time to collision: use roc if available, else estimate from speed
        if roc < -1 and distance > 0:
            ttc = round(distance / abs(roc), 1)
        elif speed > 0 and distance > 0:
            ttc = round(distance / (speed * 100), 1)   # speed m/s → cm/s
        else:
            ttc = None

        if score > 80:   action = 'STOP'
        elif score > 60: action = 'SLOW_DOWN'
        elif score > 30: action = 'CAUTION'
        else:            action = 'SAFE'

        return {
            'danger_score':       round(score, 2),
            'recommended_action': action,
            'time_to_collision':  ttc,
            'confidence':         0.9,
            'model_source':       model_source,
            'message': f"{'Path clear' if action == 'SAFE' else action} - {score:.0f}% danger"
        }

    def _danger_score(self, distance, roc, risk_mult=1.0):
        """Rule-based fallback danger score, adjusted for object risk."""
        score = 0.0
        eff_dist = distance / risk_mult   # scale distance by risk

        if eff_dist < 30:    score += 70
        elif eff_dist < 100: score += 50
        elif eff_dist < 200: score += 25
        elif eff_dist < 350: score += 10

        if roc < -20:   score += 30
        elif roc < -10: score += 20
        elif roc < -5:  score += 10
        elif roc < 0:   score += 5

        return score

    # ── Anomaly Detection ─────────────────────────────────────────────────────

    def detect_anomaly(self, data):
        """
        Detect device anomalies from telemetry readings.

        FIX from original:
          - confidence was incorrectly set equal to anomaly_score.
            Isolation Forest's score_samples() returns negative log-likelihood;
            we convert to [0,1] and then compute confidence as distance from
            the decision boundary (0.5), clamped to [0,1].
          - model_source tracked
        """
        temp    = _clamp(float(data.get('temperature_c',  35)),   0, 150,  'temperature_c')
        battery = _clamp(float(data.get('battery_level',  80)),   0, 100,  'battery_level')
        cpu     = _clamp(float(data.get('cpu_usage',      40)),   0, 100,  'cpu_usage')
        errors  = _clamp(float(data.get('error_count',     0)),   0, 9999, 'error_count')
        rssi    = _clamp(float(data.get('rssi',          -50)), -120,  0,  'rssi')

        model, scaler = _load_bundle('anomaly_detector')
        model_source  = 'fallback'

        if model:
            try:
                features = np.array([[temp, battery, cpu, errors, rssi]])
                if scaler:
                    features = scaler.transform(features)

                prediction = model.predict(features)[0]
                is_anomaly = bool(prediction == -1)

                # score_samples returns negative log-likelihood (more negative = more anomalous)
                # Normalise to [0, 1]: we use abs then clip; higher value = more anomalous
                raw_score  = float(model.score_samples(features)[0])
                # Typical range for Isolation Forest is roughly [-0.5, 0.5]
                # Map to [0, 1]: anomaly_score = 0.5 - raw_score (clipped)
                anomaly_score = float(np.clip(0.5 - raw_score, 0.0, 1.0))

                # Confidence = how far the score is from the ambiguous midpoint (0.5)
                # score near 0 or near 1 → high confidence; score near 0.5 → low
                confidence = float(np.clip(abs(anomaly_score - 0.5) * 2, 0.0, 1.0))

                model_source = 'ml_model'

            except Exception as e:
                print(f"[MLService] Anomaly model error: {e}")
                is_anomaly, anomaly_score = self._anomaly_rules(temp, battery, cpu, errors)
                confidence = 0.6
        else:
            is_anomaly, anomaly_score = self._anomaly_rules(temp, battery, cpu, errors)
            confidence = 0.6

        health    = round(100 - (anomaly_score * 100), 1)
        severity  = (
            'critical' if anomaly_score > 0.8 else
            'high'     if anomaly_score > 0.6 else
            'medium'   if anomaly_score > 0.4 else
            'low'
        )

        return {
            'is_anomaly':          is_anomaly,
            'anomaly_score':       round(anomaly_score, 3),
            'confidence':          round(confidence, 3),
            'severity':            severity,
            'device_health_score': health,
            'model_source':        model_source,
            'message': f"{'Anomaly detected' if is_anomaly else 'Device normal'} (health: {health}%)"
        }

    def _anomaly_rules(self, temp, battery, cpu, errors):
        issues = 0
        if temp > 80:      issues += 2
        elif temp > 70:    issues += 1
        if battery < 10:   issues += 2
        elif battery < 20: issues += 1
        if cpu > 95:       issues += 2
        elif cpu > 85:     issues += 1
        if errors > 10:    issues += 2
        elif errors > 5:   issues += 1
        score = min(issues / 7.0, 1.0)
        return score > 0.4, score

    # ── Environment Classification ────────────────────────────────────────────

    def classify_environment(self, data):
        """
        Classify the navigation environment from sensor aggregates.

        Changes from original:
          - Feature validation / clamping
          - model_source tracked
          - Hardened confidence: model returns 0.85; fallback returns 0.70
        """
        light_avg  = _clamp(float(data.get('ambient_light_avg',         500)), 0,   10000, 'ambient_light_avg')
        light_var  = _clamp(float(data.get('ambient_light_variance',    100)), 0,   10000, 'ambient_light_variance')
        det_freq   = _clamp(float(data.get('detection_frequency',         2)), 0,     100, 'detection_frequency')
        avg_dist   = _clamp(float(data.get('average_obstacle_distance', 150)), 0,    1000, 'average_obstacle_distance')
        complexity = _clamp(float(data.get('proximity_pattern_complexity', 5)), 0,     10, 'proximity_pattern_complexity')
        dist_var   = _clamp(float(data.get('distance_variance',          50)), 0,    1000, 'distance_variance')

        model, scaler = _load_bundle('environment_classifier')
        model_source  = 'fallback'

        if model:
            try:
                features = np.array([[light_avg, light_var, det_freq,
                                      avg_dist, complexity, dist_var]])
                if scaler:
                    features = scaler.transform(features)
                env_type     = str(model.predict(features)[0])
                conf         = 0.85
                model_source = 'ml_model'
            except Exception as e:
                print(f"[MLService] Environment model error: {e}")
                env_type, conf = self._environment_rules(light_avg, avg_dist, complexity)
        else:
            env_type, conf = self._environment_rules(light_avg, avg_dist, complexity)

        lighting         = 'bright' if light_avg > 700 else 'dim' if light_avg > 300 else 'dark'
        complexity_level = 'high'   if complexity > 7  else 'medium' if complexity > 4 else 'low'

        return {
            'environment_type':   env_type,
            'lighting_condition': lighting,
            'complexity_level':   complexity_level,
            'confidence':         conf,
            'model_source':       model_source,
            'message': f"{env_type} - {lighting} lighting - {complexity_level} complexity"
        }

    def _environment_rules(self, light_avg, avg_dist, complexity):
        if light_avg > 700 and avg_dist > 200: return 'outdoor',       0.75
        if light_avg < 200:                    return 'dark_indoor',   0.70
        if complexity > 6:                     return 'complex_indoor', 0.70
        return 'indoor', 0.70


ml_service = MLService()