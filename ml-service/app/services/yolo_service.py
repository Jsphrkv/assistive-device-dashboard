import base64
import numpy as np
from ml_models.model_loader import get_yolo_model_path

# YOLO class labels (COCO dataset, 80 classes)
YOLO_LABELS = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
    'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
    'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
    'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

# Map YOLO labels to navigation-relevant object types
LABEL_TO_OBJECT_TYPE = {
    'person':        'person',
    'bicycle':       'vehicle',
    'car':           'vehicle',
    'motorcycle':    'vehicle',
    'bus':           'vehicle',
    'truck':         'vehicle',
    'chair':         'obstacle',
    'couch':         'obstacle',
    'dining table':  'obstacle',
    'bed':           'obstacle',
    'toilet':        'obstacle',
    'door':          'door',
    'stairs':        'stairs',
    'potted plant':  'obstacle',
    'backpack':      'obstacle',
    'suitcase':      'obstacle',
    'bottle':        'obstacle',
    'bench':         'obstacle',
    'traffic light': 'landmark',
    'stop sign':     'landmark',
    'fire hydrant':  'obstacle',
    'dog':           'animal',
    'cat':           'animal',
}

# Navigation priority: higher = alert sooner
OBJECT_PRIORITY = {
    'person':   10,
    'vehicle':  9,
    'stairs':   8,
    'animal':   6,
    'door':     5,
    'obstacle': 4,
    'landmark': 2,
}


def _no_detection(message: str) -> dict:
    """Shared helper for all early-exit / error paths."""
    return {
        'detected':        False,
        'object_type':     'none',
        'raw_label':       'none',
        'category':        'navigation',
        'confidence':      0.0,
        'all_detections':  [],
        'box':             None,
        'message':         message,
    }


def _iou(box_a, box_b):
    """
    Compute IoU between two [x1, y1, x2, y2] boxes.
    Used for manual NMS fallback if cv2.dnn.NMSBoxes unavailable.
    """
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def run_yolo(image_data: str, conf_threshold: float = 0.4, nms_threshold: float = 0.45) -> dict:
    """
    Run YOLOv5 ONNX inference on a base64-encoded JPEG image.

    Improvements over original:
      - Bounding box [x, y, w, h] preserved in each detection for Option A
        distance estimation in detection_coordinator.py
      - Proper NMS applied to remove duplicate detections of same object
      - Detections sorted by navigation priority, not just confidence
      - Image preprocessing validates shape before proceeding
      - Configurable conf_threshold and nms_threshold parameters

    Args:
        image_data     : Base64-encoded JPEG string
        conf_threshold : Minimum confidence to keep a detection (default 0.4)
        nms_threshold  : IoU threshold for NMS suppression (default 0.45)

    Returns:
        dict with detected, object_type, raw_label, category, confidence,
        all_detections (list), box ([x, y, w, h] in original image pixels), message
    """
    model_path = get_yolo_model_path()

    if not model_path:
        return _no_detection('YOLO model not available - using fallback')

    try:
        import onnxruntime as ort
        import cv2

        # ── Session init ──────────────────────────────────────────────────────
        session = ort.InferenceSession(model_path)
        inp     = session.get_inputs()[0]

        # Diagnostic (remove after confirming float32 works)
        print(f"[YOLO DIAG] Input name:    {inp.name}")
        print(f"[YOLO DIAG] Input shape:   {inp.shape}")
        print(f"[YOLO DIAG] Input type:    {inp.type}")
        print(f"[YOLO DIAG] ORT version:   {ort.__version__}")
        print(f"[YOLO DIAG] NumPy version: {np.__version__}")

        # ── Decode + validate image ───────────────────────────────────────────
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img       = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return _no_detection('Failed to decode image')

        orig_h, orig_w = img.shape[:2]
        if orig_h == 0 or orig_w == 0:
            return _no_detection('Image has zero dimension')

        # ── Preprocess ────────────────────────────────────────────────────────
        # Auto-detect the dtype the model expects (float32 or float16).
        # Always normalise in float32 first for precision, then cast at the end.
        model_dtype = np.float16 if 'float16' in inp.type else np.float32

        img_resized = cv2.resize(img, (640, 640))
        img_rgb     = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_norm    = img_rgb.astype(np.float32) / 255.0          # float32 precision
        img_input   = np.transpose(img_norm, (2, 0, 1))[np.newaxis, :].astype(model_dtype)

        # ── Inference ─────────────────────────────────────────────────────────
        input_name = inp.name
        outputs    = session.run(None, {input_name: img_input})

        # ── Parse detections ──────────────────────────────────────────────────
        # YOLOv5 ONNX output shape: (1, 25200, 85)
        #   det[0:4]  = x_center, y_center, width, height  (in 640x640 space)
        #   det[4]    = objectness
        #   det[5:85] = 80 class scores
        detections  = outputs[0][0]

        # Scale factors to map 640x640 coords back to original image resolution
        scale_x = orig_w / 640.0
        scale_y = orig_h / 640.0

        raw_boxes   = []   # [x, y, w, h] in original image pixels — for NMS
        xyxy_boxes  = []   # [x1, y1, x2, y2] — used internally for NMS IoU
        raw_scores  = []
        raw_classes = []

        for det in detections:
            objectness = float(det[4])
            if objectness < conf_threshold:
                continue

            class_scores = det[5:]
            class_id     = int(np.argmax(class_scores))
            class_conf   = float(class_scores[class_id])
            conf         = objectness * class_conf

            if conf < conf_threshold:
                continue

            # YOLO bbox is x_center, y_center, w, h in 640x640 space
            xc, yc, bw, bh = det[0], det[1], det[2], det[3]

            # Convert to original image pixel coordinates
            xc_orig = xc * scale_x
            yc_orig = yc * scale_y
            bw_orig = bw * scale_x
            bh_orig = bh * scale_y

            x1 = xc_orig - bw_orig / 2
            y1 = yc_orig - bh_orig / 2
            x2 = xc_orig + bw_orig / 2
            y2 = yc_orig + bh_orig / 2

            # Clamp to image bounds
            x1 = max(0.0, x1);  y1 = max(0.0, y1)
            x2 = min(float(orig_w), x2);  y2 = min(float(orig_h), y2)

            bw_clamped = x2 - x1
            bh_clamped = y2 - y1
            if bw_clamped <= 0 or bh_clamped <= 0:
                continue

            raw_boxes.append([x1, y1, bw_clamped, bh_clamped])   # [x, y, w, h]
            xyxy_boxes.append([x1, y1, x2, y2])
            raw_scores.append(conf)
            raw_classes.append(class_id)

        if not raw_boxes:
            return _no_detection('No objects detected above threshold')

        # ── NMS ───────────────────────────────────────────────────────────────
        # cv2.dnn.NMSBoxes expects [x, y, w, h] format — raw_boxes already is.
        try:
            indices = cv2.dnn.NMSBoxes(
                raw_boxes,
                raw_scores,
                conf_threshold,
                nms_threshold
            )
            # OpenCV returns ndarray or list depending on version
            if hasattr(indices, 'flatten'):
                indices = indices.flatten().tolist()
            else:
                indices = [i[0] if isinstance(i, (list, tuple)) else i for i in indices]
        except Exception as nms_err:
            print(f"[YOLO] cv2.dnn.NMSBoxes failed ({nms_err}), using manual NMS")
            # Manual greedy NMS fallback
            order   = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)
            indices = []
            suppressed = set()
            for i in order:
                if i in suppressed:
                    continue
                indices.append(i)
                for j in order:
                    if j != i and j not in suppressed:
                        if _iou(xyxy_boxes[i], xyxy_boxes[j]) > nms_threshold:
                            suppressed.add(j)

        # ── Build final detection list ─────────────────────────────────────────
        all_detections = []
        for idx in indices:
            class_id    = raw_classes[idx]
            raw_label   = YOLO_LABELS[class_id] if class_id < len(YOLO_LABELS) else 'unknown'
            object_type = LABEL_TO_OBJECT_TYPE.get(raw_label, 'obstacle')
            box         = raw_boxes[idx]   # [x, y, w, h] in original image pixels

            all_detections.append({
                'label':       raw_label,
                'object_type': object_type,
                'confidence':  round(raw_scores[idx], 4),
                'box':         [round(v, 1) for v in box],   # [x, y, w, h]
                # Convenience alias used by detection_coordinator.py Option A
                'object':      raw_label,
            })

        if not all_detections:
            return _no_detection('No objects survived NMS')

        # ── Select best detection ─────────────────────────────────────────────
        # Sort by navigation priority first, confidence second.
        # This ensures a person at 0.45 confidence beats a bottle at 0.90.
        def detection_priority(d):
            prio = OBJECT_PRIORITY.get(d['object_type'], 3)
            return (prio, d['confidence'])

        all_detections.sort(key=detection_priority, reverse=True)
        best = all_detections[0]

        print(f"[YOLO] Best: {best['label']} ({best['confidence']*100:.0f}% conf) "
              f"box={best['box']} | total after NMS: {len(all_detections)}")

        return {
            'detected':        True,
            'object_type':     best['object_type'],
            'raw_label':       best['label'],
            'category':        'navigation',
            'confidence':      best['confidence'],
            'box':             best['box'],        # [x, y, w, h] for Option A
            'all_detections':  all_detections,
            'message':         f"{best['label']} detected ({best['confidence']:.2f})",
        }

    except Exception as e:
        print(f"[YOLO] Inference error: {e}")
        import traceback
        traceback.print_exc()
        return _no_detection(f"YOLO error: {str(e)}")