import axios from "axios";
import { storage } from "../utils/helpers";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

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
        error.config?.url?.includes("/auth/register");

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

  // resetPassword: (token, password) =>
  //   api.post("/auth/reset-password", { token, password }),

  logout: () => api.post("/auth/logout"),

  getCurrentUser: () => api.get("/auth/me"),

  resetPassword: async (token, password) => {
    const response = await fetch(
      "http://localhost:5000/api/auth/reset-password",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: token,
          password: password,
        }),
      },
    );

    if (!response.ok) {
      const error = await response.json();
      throw { response: { data: error } };
    }

    return response.json();
  },
};

export const deviceAPI = {
  getStatus: () => api.get("/device/status"),
  getSystemInfo: () => api.get("/device/system-info"),
};

export const detectionsAPI = {
  getAll: (limit = 50, offset = 0) =>
    api.get(`/detections?limit=${limit}&offset=${offset}`),
  getRecent: () => api.get("/detections/recent"),
  getByDate: (startDate, endDate) =>
    api.get(`/detections/by-date?start_date=${startDate}&end_date=${endDate}`),
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

export default api;
