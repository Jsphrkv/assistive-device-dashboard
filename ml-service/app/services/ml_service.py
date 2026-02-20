import numpy as np
from ml_models.model_loader import load_model


def _load_bundle(name):
    """Load model bundle and return (model, scaler) tuple."""
    bundle = load_model(name)
    if bundle and isinstance(bundle, dict):
        return bundle.get('model'), bundle.get('scaler')
    return bundle, None   # fallback: bundle is the model itself


class MLService:

    # ── Object Detection ──────────────────────────────────────────────────────

    def detect_object(self, data):
        distance = data.get('distance_cm', 0)
        conf     = data.get('detection_confidence', 0.65)

        model, scaler = _load_bundle('object_detector')
        if model:
            try:
                features = np.array([[
                    distance,
                    conf,
                    data.get('proximity_value', 0),
                    data.get('ambient_light', 0),
                ]])
                if scaler:
                    features = scaler.transform(features)
                object_detected = str(model.predict(features)[0])
            except Exception as e:
                print(f"Object model error: {e}")
                object_detected = self._object_by_distance(distance)
        else:
            object_detected = self._object_by_distance(distance)

        danger = self._distance_to_danger(distance)
        return {
            'object_detected':      object_detected,
            'distance_cm':          distance,
            'danger_level':         danger,
            'detection_confidence': conf,
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
        distance = data.get('distance_cm', 200)
        roc      = data.get('rate_of_change', 0)
        speed    = data.get('current_speed_estimate', 1.0)

        model, scaler = _load_bundle('danger_predictor')
        if model:
            try:
                features = np.array([[distance, roc,
                                      data.get('proximity_value', 0), speed]])
                if scaler:
                    features = scaler.transform(features)
                score = float(model.predict(features)[0])
            except Exception as e:
                print(f"Danger model error: {e}")
                score = self._danger_score(distance, roc)
        else:
            score = self._danger_score(distance, roc)

        score = max(0.0, min(100.0, score))
        ttc   = round(distance / abs(roc), 1) if roc < -1 and distance > 0 else None

        if score > 80:   action = 'STOP'
        elif score > 60: action = 'SLOW_DOWN'
        elif score > 30: action = 'CAUTION'
        else:            action = 'SAFE'

        return {
            'danger_score':       round(score, 2),
            'recommended_action': action,
            'time_to_collision':  ttc,
            'confidence':         0.9,
            'message': f"{'Path clear' if action == 'SAFE' else action} - {score:.0f}% danger"
        }

    def _danger_score(self, distance, roc):
        score = 0.0
        if distance < 30:    score += 70
        elif distance < 100: score += 50
        elif distance < 200: score += 25
        elif distance < 350: score += 10
        if roc < -20:   score += 30
        elif roc < -10: score += 20
        elif roc < -5:  score += 10
        elif roc < 0:   score += 5
        return score

    # ── Anomaly Detection ─────────────────────────────────────────────────────

    def detect_anomaly(self, data):
        temp    = data.get('temperature_c', 35)
        battery = data.get('battery_level', 80)
        cpu     = data.get('cpu_usage', 40)
        errors  = data.get('error_count', 0)
        rssi    = data.get('rssi', -50)

        model, scaler = _load_bundle('anomaly_detector')
        if model:
            try:
                features = np.array([[temp, battery, cpu, errors, rssi]])
                if scaler:
                    features = scaler.transform(features)
                prediction = model.predict(features)[0]
                is_anomaly = bool(prediction == -1)
                score      = float(abs(model.score_samples(features)[0]))
                score      = max(0.0, min(1.0, score))
            except Exception as e:
                print(f"Anomaly model error: {e}")
                is_anomaly, score = self._anomaly_rules(temp, battery, cpu, errors)
        else:
            is_anomaly, score = self._anomaly_rules(temp, battery, cpu, errors)

        health   = round(100 - (score * 100), 1)
        severity = 'critical' if score > 0.8 else 'high' if score > 0.6 else 'medium' if score > 0.4 else 'low'

        return {
            'is_anomaly':          is_anomaly,
            'anomaly_score':       round(score, 3),
            'confidence':          round(score, 3),
            'severity':            severity,
            'device_health_score': health,
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
        light_avg  = data.get('ambient_light_avg', 500)
        light_var  = data.get('ambient_light_variance', 100)
        det_freq   = data.get('detection_frequency', 2)
        avg_dist   = data.get('average_obstacle_distance', 150)
        complexity = data.get('proximity_pattern_complexity', 5)
        dist_var   = data.get('distance_variance', 50)

        model, scaler = _load_bundle('environment_classifier')
        if model:
            try:
                features = np.array([[light_avg, light_var, det_freq,
                                      avg_dist, complexity, dist_var]])
                if scaler:
                    features = scaler.transform(features)
                env_type = str(model.predict(features)[0])
                conf     = 0.85
            except Exception as e:
                print(f"Environment model error: {e}")
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
            'message': f"{env_type} - {lighting} lighting - {complexity_level} complexity"
        }

    def _environment_rules(self, light_avg, avg_dist, complexity):
        if light_avg > 700 and avg_dist > 200: return 'outdoor', 0.75
        if light_avg < 200:                    return 'dark_indoor', 0.70
        if complexity > 6:                     return 'complex_indoor', 0.70
        return 'indoor', 0.70


ml_service = MLService()