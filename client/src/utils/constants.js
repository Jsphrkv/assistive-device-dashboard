// User Roles
export const ROLES = {
  ADMIN: "admin",
  USER: "user",
};

// Danger Levels
export const DANGER_LEVELS = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
};

// Alert Types
export const ALERT_TYPES = {
  AUDIO: "Audio",
  VIBRATION: "Vibration",
  BOTH: "Both",
};

// Obstacle Types
export const OBSTACLE_TYPES = {
  PERSON: "Person",
  WALL: "Wall",
  OBJECT: "Object",
  STAIRS: "Stairs",
};

// Distance Thresholds (in cm)
export const DISTANCE_THRESHOLDS = [50, 100, 150, 200];

// Alert Mode Options
export const ALERT_MODE_OPTIONS = [
  { value: "audio", label: "Audio Only" },
  { value: "vibration", label: "Vibration Only" },
  { value: "both", label: "Audio + Vibration" },
];

// Chart Colors
export const CHART_COLORS = {
  PRIMARY: "#3b82f6",
  SUCCESS: "#10b981",
  WARNING: "#f59e0b",
  DANGER: "#ef4444",
  INFO: "#06b6d4",
};

// Navigation Tabs
export const NAV_TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "logs", label: "Detection Logs" },
  { id: "statistics", label: "Statistics" },
  { id: "camera", label: "Live Camera" },
  { id: "settings", label: "Settings" },
  { id: "device", label: "My Device" },
];

// Table Pagination
export const ITEMS_PER_PAGE = 10;

// Refresh Intervals (in ms)
export const REFRESH_INTERVALS = {
  DEVICE_STATUS: 5000,
  DETECTION_LOGS: 10000,
  STATISTICS: 30000,
  CAMERA: 3000,
};

export default {
  ROLES,
  DANGER_LEVELS,
  ALERT_TYPES,
  OBSTACLE_TYPES,
  DISTANCE_THRESHOLDS,
  ALERT_MODE_OPTIONS,
  CHART_COLORS,
  NAV_TABS,
  ITEMS_PER_PAGE,
  REFRESH_INTERVALS,
};
