"""Object detection categories and priorities for assistive device"""

DETECTION_CATEGORIES = {
    # Critical Safety (Red - Immediate action required)
    'person': {
        'category': 'critical',
        'priority': 1,
        'color': 'red',
        'alert': 'audio+vibration',
        'icon': '👤',
        'description': 'Person detected'
    },
    'vehicle': {
        'category': 'critical',
        'priority': 1,
        'color': 'red',
        'alert': 'audio+vibration',
        'icon': '🚗',
        'description': 'Vehicle detected'
    },
    'stairs_down': {
        'category': 'critical',
        'priority': 1,
        'color': 'red',
        'alert': 'audio+vibration',
        'icon': '🪜',
        'description': 'Stairs descending'
    },
    'pothole': {
        'category': 'critical',
        'priority': 1,
        'color': 'red',
        'alert': 'audio+vibration',
        'icon': '🕳️',
        'description': 'Pothole detected'
    },
    'curb': {
        'category': 'critical',
        'priority': 1,
        'color': 'red',
        'alert': 'audio+vibration',
        'icon': '🛑',
        'description': 'Curb/step detected'
    },
    
    # Navigation Obstacles (Orange - Caution)
    'stairs_up': {
        'category': 'navigation',
        'priority': 2,
        'color': 'orange',
        'alert': 'audio',
        'icon': '🪜',
        'description': 'Stairs ascending'
    },
    'wall': {
        'category': 'navigation',
        'priority': 2,
        'color': 'orange',
        'alert': 'audio',
        'icon': '🧱',
        'description': 'Wall detected'
    },
    'door': {
        'category': 'navigation',
        'priority': 2,
        'color': 'orange',
        'alert': 'audio',
        'icon': '🚪',
        'description': 'Door detected'
    },
    'pole': {
        'category': 'navigation',
        'priority': 2,
        'color': 'orange',
        'alert': 'audio',
        'icon': '📫',
        'description': 'Pole/post detected'
    },
    'furniture': {
        'category': 'navigation',
        'priority': 2,
        'color': 'orange',
        'alert': 'audio',
        'icon': '🪑',
        'description': 'Furniture detected'
    },
    'obstacle': {
        'category': 'navigation',
        'priority': 2,
        'color': 'orange',
        'alert': 'audio',
        'icon': '⚠️',
        'description': 'General obstacle'
    },
    
    # Environmental (Yellow - Awareness)
    'bicycle': {
        'category': 'environmental',
        'priority': 3,
        'color': 'yellow',
        'alert': 'audio',
        'icon': '🚲',
        'description': 'Bicycle detected'
    },
    'animal': {
        'category': 'environmental',
        'priority': 3,
        'color': 'yellow',
        'alert': 'audio',
        'icon': '🐕',
        'description': 'Animal detected'
    },
    'tree': {
        'category': 'environmental',
        'priority': 3,
        'color': 'yellow',
        'alert': 'audio',
        'icon': '🌲',
        'description': 'Tree/plant detected'
    },
    
    # Unknown (Gray - General detection)
    'moving_object': {
        'category': 'unknown',
        'priority': 4,
        'color': 'gray',
        'alert': 'audio',
        'icon': '🔄',
        'description': 'Moving object'
    },
    'unknown': {
        'category': 'unknown',
        'priority': 5,
        'color': 'gray',
        'alert': 'audio',
        'icon': '❓',
        'description': 'Unknown object'
    },
}

def get_detection_info(object_type):
    """Get detection category information"""
    return DETECTION_CATEGORIES.get(object_type, DETECTION_CATEGORIES['unknown'])

def get_danger_level_from_object(object_type, distance_cm):
    """Determine danger level based on object and distance"""
    info = get_detection_info(object_type)
    
    if info['category'] == 'critical':
        if distance_cm < 100:
            return 'High'
        elif distance_cm < 200:
            return 'Medium'
        else:
            return 'Low'
    elif info['category'] == 'navigation':
        if distance_cm < 50:
            return 'High'
        elif distance_cm < 150:
            return 'Medium'
        else:
            return 'Low'
    else:
        return 'Low'

def get_alert_type_from_object(object_type, distance_cm):
    """Determine alert type based on object and distance"""
    info = get_detection_info(object_type)
    
    if info['category'] == 'critical' and distance_cm < 150:
        return 'Both'
    elif distance_cm < 100:
        return 'Vibration'
    else:
        return 'Audio'