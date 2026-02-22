import base64
import numpy as np
from ml_models.model_loader import get_yolo_model_path

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

LABEL_TO_OBJECT_TYPE = {
    'person': 'person', 'bicycle': 'vehicle', 'car': 'vehicle',
    'motorcycle': 'vehicle', 'bus': 'vehicle', 'truck': 'vehicle',
    'chair': 'obstacle', 'couch': 'obstacle', 'dining table': 'obstacle',
    'bed': 'obstacle', 'toilet': 'obstacle', 'door': 'door',
    'stairs': 'stairs', 'potted plant': 'obstacle', 'backpack': 'obstacle',
    'suitcase': 'obstacle', 'bottle': 'obstacle', 'bench': 'obstacle',
    'traffic light': 'landmark', 'stop sign': 'landmark',
    'fire hydrant': 'obstacle', 'dog': 'animal', 'cat': 'animal',
}

OBJECT_PRIORITY = {
    'person': 10, 'vehicle': 9, 'stairs': 8, 'animal': 6,
    'door': 5, 'obstacle': 4, 'landmark': 2,
}


def _no_detection(message):
    return {
        'detected': False, 'object_type': 'none', 'raw_label': 'none',
        'category': 'navigation', 'confidence': 0.0,
        'all_detections': [], 'box': None, 'message': message,
    }


def _iou(a, b):
    xa = max(a[0], b[0]); ya = max(a[1], b[1])
    xb = min(a[2], b[2]); yb = min(a[3], b[3])
    inter = max(0.0, xb - xa) * max(0.0, yb - ya)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def run_yolo(image_data, conf_threshold=0.4, nms_threshold=0.45):
    model_path = get_yolo_model_path()
    if not model_path:
        return _no_detection('YOLO model not available')

    try:
        import onnxruntime as ort
        import cv2

        session = ort.InferenceSession(model_path)
        inp = session.get_inputs()[0]

        print(f"[YOLO DIAG] Input name: {inp.name} | shape: {inp.shape} | type: {inp.type}")
        print(f"[YOLO DIAG] ORT: {ort.__version__} | NumPy: {np.__version__}")

        # Decode image — cv2.imdecode always returns BGR
        img_bytes = base64.b64decode(image_data)
        img = cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return _no_detection('Failed to decode image')

        orig_h, orig_w = img.shape[:2]
        if orig_h == 0 or orig_w == 0:
            return _no_detection('Image has zero dimension')

        # Preprocess — normalise in float32, cast to model dtype at end
        # This prevents precision loss when model expects float16
        model_dtype = np.float16 if 'float16' in inp.type else np.float32
        img_resized = cv2.resize(img, (640, 640))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_input = np.transpose(
            img_rgb.astype(np.float32) / 255.0, (2, 0, 1)
        )[np.newaxis, :].astype(model_dtype)

        outputs = session.run(None, {inp.name: img_input})
        detections = outputs[0][0]

        scale_x = orig_w / 640.0
        scale_y = orig_h / 640.0

        raw_boxes = []; xyxy_boxes = []; raw_scores = []; raw_classes = []

        for det in detections:
            # FIX: Cast ALL values to native Python float immediately.
            # When model runs float16, det values are np.float16.
            # Flask's jsonify() cannot serialize np.float16 —
            # this was causing "Object of type float16 is not JSON serializable".
            objectness = float(det[4])
            if objectness < conf_threshold:
                continue

            class_id = int(np.argmax(det[5:]))
            conf = float(objectness) * float(det[5 + class_id])

            if conf < conf_threshold:
                continue

            # Convert from 640x640 space to original image pixels
            xc = float(det[0]) * scale_x
            yc = float(det[1]) * scale_y
            bw = float(det[2]) * scale_x
            bh = float(det[3]) * scale_y

            x1 = max(0.0, xc - bw / 2)
            y1 = max(0.0, yc - bh / 2)
            x2 = min(float(orig_w), xc + bw / 2)
            y2 = min(float(orig_h), yc + bh / 2)
            bwc = x2 - x1; bhc = y2 - y1

            if bwc <= 0 or bhc <= 0:
                continue

            raw_boxes.append([x1, y1, bwc, bhc])   # [x, y, w, h] native floats
            xyxy_boxes.append([x1, y1, x2, y2])
            raw_scores.append(float(conf))          # native float — JSON-safe
            raw_classes.append(class_id)

        if not raw_boxes:
            return _no_detection('No objects detected above threshold')

        # NMS — cv2.dnn.NMSBoxes expects [x, y, w, h] format
        try:
            indices = cv2.dnn.NMSBoxes(raw_boxes, raw_scores, conf_threshold, nms_threshold)
            if hasattr(indices, 'flatten'):
                indices = indices.flatten().tolist()
            else:
                indices = [i[0] if isinstance(i, (list, tuple)) else i for i in indices]
        except Exception as e:
            print(f"[YOLO] NMS fallback: {e}")
            order = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)
            indices = []; suppressed = set()
            for i in order:
                if i in suppressed: continue
                indices.append(i)
                for j in order:
                    if j != i and j not in suppressed:
                        if _iou(xyxy_boxes[i], xyxy_boxes[j]) > nms_threshold:
                            suppressed.add(j)

        all_detections = []
        for idx in indices:
            cid = raw_classes[idx]
            label = YOLO_LABELS[cid] if cid < len(YOLO_LABELS) else 'unknown'
            otype = LABEL_TO_OBJECT_TYPE.get(label, 'obstacle')
            box = [round(v, 1) for v in raw_boxes[idx]]   # JSON-safe

            all_detections.append({
                'label': label, 'object_type': otype,
                'confidence': round(raw_scores[idx], 4),   # native float — JSON-safe
                'box': box,    # [x, y, w, h]
                'object': label,
            })

        if not all_detections:
            return _no_detection('No objects survived NMS')

        all_detections.sort(
            key=lambda d: (OBJECT_PRIORITY.get(d['object_type'], 3), d['confidence']),
            reverse=True
        )
        best = all_detections[0]

        print(f"[YOLO] {best['label']} ({best['confidence']*100:.0f}%) "
              f"box={best['box']} | {len(all_detections)} after NMS")

        return {
            'detected': True,
            'object_type': best['object_type'],
            'raw_label': best['label'],
            'category': 'navigation',
            'confidence': best['confidence'],   # native float — JSON-safe
            'box': best['box'],
            'all_detections': all_detections,
            'message': f"{best['label']} detected ({best['confidence']:.2f})",
        }

    except Exception as e:
        print(f"[YOLO] Inference error: {e}")
        import traceback; traceback.print_exc()
        return _no_detection(f"YOLO error: {str(e)}")