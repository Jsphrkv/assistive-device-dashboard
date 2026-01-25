/**
 * ML Service - Interface for ML API endpoints
 */

const ML_API_BASE = "https://assistive-device-dashboard.onrender.com/api/ml";

class MLService {
  /**
   * Check ML service health
   */
  async checkHealth() {
    const response = await fetch(`${ML_API_BASE}/health`);
    return response.json();
  }

  /**
   * Get list of available models
   */
  async getModels() {
    const response = await fetch(`${ML_API_BASE}/models`);
    return response.json();
  }

  /**
   * Detect anomalies in device telemetry
   */
  async detectAnomaly(telemetry) {
    const response = await fetch(`${ML_API_BASE}/detect/anomaly`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(telemetry),
    });
    return response.json();
  }

  /**
   * Predict maintenance needs
   */
  async predictMaintenance(deviceInfo) {
    const response = await fetch(`${ML_API_BASE}/predict/maintenance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(deviceInfo),
    });
    return response.json();
  }

  /**
   * Recognize user activity
   */
  async recognizeActivity(sensorData) {
    const response = await fetch(`${ML_API_BASE}/recognize/activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sensorData),
    });
    return response.json();
  }

  /**
   * Comprehensive device analysis
   */
  async analyzeDevice(data) {
    const response = await fetch(`${ML_API_BASE}/analyze/device`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return response.json();
  }

  /**
   * Classify device type
   */
  async classifyDevice(features) {
    const response = await fetch(`${ML_API_BASE}/predict/device`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ features }),
    });
    return response.json();
  }
}

export default new MLService();
