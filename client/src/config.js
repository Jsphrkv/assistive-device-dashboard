export const config = {
  api: {
    baseUrl:
      import.meta.env.VITE_API_URL ||
      (import.meta.env.MODE === "development"
        ? "http://localhost:5000/api"
        : "https://assistive-device-dashboard.onrender.com/api"),
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || "Assistive Device Dashboard",
    version: import.meta.env.VITE_APP_VERSION || "1.0.0",
  },
  camera: {
    refreshInterval:
      parseInt(import.meta.env.VITE_CAMERA_REFRESH_INTERVAL) || 3000,
  },
};

export default config;
