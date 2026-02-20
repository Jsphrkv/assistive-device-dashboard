import base64
import numpy as np
from ml_models.model_loader import get_yolo_model_path

# YOLO class labels
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

# Map YOLO labels to navigation-relevant categories
LABEL_TO_OBJECT_TYPE = {
    'person':       'person',
    'bicycle':      'vehicle',
    'car':          'vehicle',
    'motorcycle':   'vehicle',
    'bus':          'vehicle',
    'truck':        'vehicle',
    'chair':        'obstacle',
    'couch':        'obstacle',
    'dining table': 'obstacle',
    'bed':          'obstacle',
    'toilet':       'obstacle',
    'door':         'door',
    'stairs':       'stairs',
}


def run_yolo(image_data: str) -> dict:
    """
    Run YOLO inference on a base64-encoded JPEG image.
    Falls back to a safe default if model is not loaded.
    """
    model_path = get_yolo_model_path()

    if not model_path:
        return {
            'detected':       False,
            'object_type':    'none',
            'raw_label':      'none',
            'category':       'navigation',
            'confidence':     0.0,
            'all_detections': [],
            'message':        'YOLO model not available - using fallback'
        }

    try:
        import onnxruntime as ort
        import cv2

        # Decode base64 image
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Failed to decode image")

        # Preprocess for YOLOv5n
        img_resized = cv2.resize(img, (640, 640))
        img_rgb     = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_norm    = img_rgb.astype(np.float32) / 255.0
        img_input   = np.transpose(img_norm, (2, 0, 1))[np.newaxis, :]

        # Run inference
        session = ort.InferenceSession(model_path)
        input_name = session.get_inputs()[0].name
        outputs    = session.run(None, {input_name: img_input})

        # Parse detections [x1,y1,x2,y2,conf,class]
        detections     = outputs[0][0]
        conf_threshold = 0.4
        all_detections = []

        for det in detections:
            conf = float(det[4])
            if conf < conf_threshold:
                continue
            class_id   = int(det[5])
            raw_label  = YOLO_LABELS[class_id] if class_id < len(YOLO_LABELS) else 'unknown'
            object_type = LABEL_TO_OBJECT_TYPE.get(raw_label, 'obstacle')
            all_detections.append({
                'label':       raw_label,
                'object_type': object_type,
                'confidence':  conf
            })

        if not all_detections:
            return {
                'detected':       False,
                'object_type':    'none',
                'raw_label':      'none',
                'category':       'navigation',
                'confidence':     0.0,
                'all_detections': [],
                'message':        'No objects detected'
            }

        # Return highest confidence detection
        best = max(all_detections, key=lambda x: x['confidence'])
        return {
            'detected':       True,
            'object_type':    best['object_type'],
            'raw_label':      best['label'],
            'category':       'navigation',
            'confidence':     best['confidence'],
            'all_detections': all_detections,
            'message':        f"{best['label']} detected ({best['confidence']:.2f})"
        }

    except Exception as e:
        print(f"[YOLO] Inference error: {e}")
        return {
            'detected':       False,
            'object_type':    'none',
            'raw_label':      'none',
            'category':       'navigation',
            'confidence':     0.0,
            'all_detections': [],
            'message':        f"YOLO error: {str(e)}"
        }