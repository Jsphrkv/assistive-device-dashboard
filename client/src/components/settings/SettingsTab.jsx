import React, { useState, useEffect } from "react";
import SettingsForm from "./SettingsForm";
import { settingsAPI } from "../../services/api";

const SettingsTab = ({ currentUser }) => {
  const [settings, setSettings] = useState({
    sensitivity: 75,
    distanceThreshold: 100,
    alertMode: "both",
    ultrasonicEnabled: true,
    cameraEnabled: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.get();
      if (response.data) {
        setSettings(response.data);
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (key, value) => {
    if (currentUser.role === "admin") {
      setSettings((prev) => ({ ...prev, [key]: value }));
    } else if (currentUser.role === "user") {
      // Users can only change sensitivity and alertMode
      if (key === "sensitivity" || key === "alertMode") {
        setSettings((prev) => ({ ...prev, [key]: value }));
      }
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    try {
      const response = await settingsAPI.update(settings);

      if (response.data) {
        setMessage("Settings saved successfully!");
      }
    } catch (error) {
      setMessage("Failed to save settings");
      console.error("Error saving settings:", error);
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(""), 3000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">
        Settings & Configuration
      </h2>

      {message && (
        <div
          className={`p-4 rounded-lg ${
            message.includes("success")
              ? "bg-green-50 text-green-800"
              : "bg-red-50 text-red-800"
          }`}
        >
          {message}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <SettingsForm
          settings={settings}
          onChange={handleChange}
          userRole={currentUser.role}
          onSave={handleSave}
          loading={saving}
        />
      </div>
    </div>
  );
};

export default SettingsTab;
