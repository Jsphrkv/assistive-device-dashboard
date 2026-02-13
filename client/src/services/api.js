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
  getDaily: (days = 7) => api.get(`/statistics/daily?days=${days}`),
  getObstacles: () => api.get("/statistics/obstacles"),
  getHourly: () => api.get("/statistics/hourly"),
  getSummary: () => api.get("/statistics/summary"),
};

export const settingsAPI = {
  get: () => api.get("/settings"),
  update: (settings) => api.put("/settings", settings),
  reset: () => api.post("/settings/reset"),
};

export const mlAPI = {
  // Anomaly Detection
  detectAnomaly: (telemetryData) =>
    api.post("/ml/detect/anomaly", telemetryData),

  // Activity Recognition
  recognizeActivity: (sensorData) =>
    api.post("/ml/recognize/activity", sensorData),

  // Maintenance Prediction
  predictMaintenance: (deviceData) =>
    api.post("/ml/predict/maintenance", deviceData),

  // ML History (when backend is ready)
  // getHistory: (deviceId, limit = 100) =>
  //   api.get(`/ml/history/${deviceId}?limit=${limit}`),

  // // ML Statistics (when backend is ready)
  // getStatistics: (deviceId, timeRange = "24h") =>
  //   api.get(`/ml/statistics/${deviceId}?range=${timeRange}`),
  // ✅ UPDATED: Change from /ml/history to /ml-history
  getHistory: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append("limit", params.limit);
    if (params.offset) queryParams.append("offset", params.offset);
    if (params.type) queryParams.append("type", params.type);
    if (params.anomalies_only)
      queryParams.append("anomalies_only", params.anomalies_only);
    if (params.start_date) queryParams.append("start_date", params.start_date);
    if (params.end_date) queryParams.append("end_date", params.end_date);

    // ✅ Changed from /ml/history to /ml-history
    return api.get(`/ml-history?${queryParams.toString()}`);
  },

  // ✅ Changed from /ml/history/anomalies to /ml-history/anomalies
  getAnomalies: (limit = 20) => api.get(`/ml-history/anomalies?limit=${limit}`),

  // ✅ Changed from /ml/history/stats to /ml-history/stats
  getStats: (days = 7) => api.get(`/ml-history/stats?days=${days}`),
};

export default api;
