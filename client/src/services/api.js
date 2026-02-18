import axios from "axios";
import { storage } from "../utils/helpers";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "development"
    ? "http://localhost:5000/api"
    : "https://assistive-device-dashboard.onrender.com/api");

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - add token to all requests
api.interceptors.request.use(
  (config) => {
    const token = storage.get("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor - handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only redirect if NOT a login/register request
      const isAuthRequest =
        error.config?.url?.includes("/auth/login") ||
        error.config?.url?.includes("/auth/register") ||
        error.config?.url?.includes("/auth/logout");

      if (!isAuthRequest) {
        storage.remove("token");
        storage.remove("currentUser");
        window.location.href = "/";
      }
    }
    return Promise.reject(error);
  },
);

// API methods
export const authAPI = {
  login: (username, password) =>
    api.post("/auth/login", { username, password }),

  register: (username, email, password) =>
    api.post("/auth/register", { username, email, password }),

  verifyEmail: (token) => api.post("/auth/verify-email", { token }),

  resendVerification: (email) =>
    api.post("/auth/resend-verification", { email }),

  forgotPassword: (email) => api.post("/auth/forgot-password", { email }),

  logout: () => api.post("/auth/logout"),

  getCurrentUser: () => api.get("/auth/me"),

  // Fixed resetPassword to send new_password instead of password
  resetPassword: async (token, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token, new_password: password }), // ← Changed here
    });

    if (!response.ok) {
      const error = await response.json();
      throw { response: { data: error } };
    }

    return response.json();
  },
};

export const deviceAPI = {
  getStatus: () => api.get("/devices/status"),
  getSystemInfo: () => api.get("/devices/system-info"),
  getAll: () => api.get("/devices"),
  create: (deviceData) => api.post("/devices", deviceData),
  delete: (deviceId) => api.delete(`/devices/${deviceId}`),
  regenerateToken: (deviceId) =>
    api.post(`/devices/${deviceId}/regenerate-token`),
  completePairing: (data) => api.post("/devices/complete-pairing", data),
};

export const detectionsAPI = {
  getAll: (limit = 50, offset = 0) =>
    api.get(`/detections?limit=${limit}&offset=${offset}`),

  // Add optional limit parameter
  getRecent: (limit = 10) => api.get(`/detections/recent?limit=${limit}`),

  getByDate: (startDate, endDate) =>
    api.get(`/detections/by-date?start_date=${startDate}&end_date=${endDate}`),
  export: (params) =>
    api.get(`/detections/export?${params}`, {
      responseType: "blob",
    }),
  getCategories: () => api.get("/detections/categories"),
};

export const statisticsAPI = {
  getDaily: async (days = 7) => {
    // ✅ FIXED: Use path parameter instead of query parameter
    const response = await api.get(`/statistics/daily/${days}`);
    return response;
  },

  getObstacles: async () => {
    const response = await api.get("/statistics/obstacles");
    return response;
  },

  getHourly: async (hours = 24) => {
    const response = await api.get(`/statistics/hourly`); // Remove hours param if not used
    return response;
  },

  getSummary: async () => {
    const response = await api.get("/statistics/summary");
    return response;
  },
};

export const settingsAPI = {
  get: () => api.get("/settings"),
  update: (settings) => api.put("/settings", settings),
  reset: () => api.post("/settings/reset"),
};

export const cameraAPI = {
  getSnapshot: () => api.get("/camera/snapshot"),
};

export const mlAPI = {
  // ========== Anomaly Detection ==========
  detectAnomaly: (telemetryData) =>
    api.post("/ml/detect/anomaly", telemetryData),

  // ========== Maintenance Prediction ==========
  predictMaintenance: (deviceData) =>
    api.post("/ml/predict/maintenance", deviceData),

  // ========== Object Detection ==========
  detectObject: (detectionData) =>
    api.post("/ml/detect/object", {
      device_id: detectionData.device_id,
      distance_cm: detectionData.distance_cm,
      detection_confidence: detectionData.detection_confidence || 0.85,
      proximity_value: detectionData.proximity_value || 5000,
      ambient_light: detectionData.ambient_light || 400,
      detection_source: detectionData.detection_source || "ultrasonic",
    }),

  // ========== Danger Prediction (NEW) ==========
  predictDanger: (dangerData) =>
    api.post("/ml/predict/danger", {
      device_id: dangerData.device_id,
      distance_cm: dangerData.distance_cm,
      rate_of_change: dangerData.rate_of_change,
      proximity_value: dangerData.proximity_value || 5000,
      object_type: dangerData.object_type || "obstacle",
      current_speed_estimate: dangerData.current_speed_estimate || 1.0,
    }),

  // ========== Environment Classification (NEW) ==========
  classifyEnvironment: (environmentData) =>
    api.post("/ml/classify/environment", {
      device_id: environmentData.device_id,
      ambient_light_avg: environmentData.ambient_light_avg,
      ambient_light_variance: environmentData.ambient_light_variance,
      detection_frequency: environmentData.detection_frequency,
      average_obstacle_distance: environmentData.average_obstacle_distance,
      proximity_pattern_complexity:
        environmentData.proximity_pattern_complexity,
      distance_variance: environmentData.distance_variance,
    }),

  // ========== ML History & Statistics ==========
  getHistory: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append("limit", params.limit);
    if (params.offset) queryParams.append("offset", params.offset);
    if (params.type) queryParams.append("type", params.type);
    if (params.anomalies_only)
      queryParams.append("anomalies_only", params.anomalies_only);
    if (params.start_date) queryParams.append("start_date", params.start_date);
    if (params.end_date) queryParams.append("end_date", params.end_date);

    return api.get(`/ml-history?${queryParams.toString()}`);
  },

  getAnomalies: (limit = 20) => api.get(`/ml-history/anomalies?limit=${limit}`),

  getStats: (days = 7) => api.get(`/ml-history/stats?days=${days}`),
  getDailySummary: (days = 7) =>
    api.get(`/ml-history/daily-summary?days=${days}`),
};

export default api;
