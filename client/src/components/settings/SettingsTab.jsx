import React, { useState, useEffect, useRef } from "react";
import SettingsForm from "./SettingsForm";
import { settingsAPI } from "../../services/api";

const APPLY_DELAY_SECONDS = 30;

const SettingsTab = ({ currentUser }) => {
  const [settings, setSettings] = useState({
    sensitivity: 75,
    distanceThreshold: 100,
    alertMode: "both",
    ultrasonicEnabled: true,
    cameraEnabled: true,
  });
  const [editMode, setEditMode] = useState(false);
  const [pendingSettings, setPendingSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [countdown, setCountdown] = useState(null);
  const countdownRef = useRef(null);

  useEffect(() => {
    fetchSettings();
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.get();
      if (response.data?.data) {
        setSettings(response.data.data);
        setPendingSettings(response.data.data);
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setPendingSettings({ ...settings });
    setEditMode(true);
    setMessage(null);
    if (countdownRef.current) clearInterval(countdownRef.current);
    setCountdown(null);
  };

  const handleCancel = () => {
    setPendingSettings({ ...settings });
    setEditMode(false);
    setMessage(null);
  };

  const handleChange = (key, value) => {
    if (!editMode) return;
    setPendingSettings((prev) => ({ ...prev, [key]: value }));
  };

  const startCountdown = () => {
    if (countdownRef.current) clearInterval(countdownRef.current);
    setCountdown(APPLY_DELAY_SECONDS);
    countdownRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(countdownRef.current);
          setCountdown(null);
          setMessage({
            type: "applied",
            text: "✅ Settings applied to device!",
          });
          setTimeout(() => setMessage(null), 4000);
          return null;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const response = await settingsAPI.update(pendingSettings);
      if (
        response.data?.message ||
        response.data?.data ||
        response.status === 200
      ) {
        setSettings({ ...pendingSettings });
        setEditMode(false);
        setMessage({
          type: "success",
          text: "✅ Settings saved successfully!",
        });
        startCountdown();
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "❌ Failed to save settings. Please try again.",
      });
      console.error("Error saving settings:", error);
      setTimeout(() => setMessage(null), 4000);
    } finally {
      setSaving(false);
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
          className={`p-4 rounded-lg border ${
            message.type === "success"
              ? "bg-green-50 border-green-200 text-green-800"
              : message.type === "applied"
                ? "bg-blue-50 border-blue-200 text-blue-800"
                : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          {message.text}
        </div>
      )}

      {countdown !== null && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-amber-800">
                ⏳ Applying settings to device...
              </p>
              <p className="text-xs text-amber-700 mt-1">
                Your device checks for new settings every 30 seconds. Changes
                will take effect shortly.
              </p>
            </div>
            <div className="text-center ml-4">
              <div className="text-3xl font-bold text-amber-600">
                {countdown}
              </div>
              <div className="text-xs text-amber-500">seconds</div>
            </div>
          </div>
          <div className="mt-3 h-1.5 bg-amber-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full transition-all duration-1000"
              style={{
                width: `${((APPLY_DELAY_SECONDS - countdown) / APPLY_DELAY_SECONDS) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <SettingsForm
          settings={pendingSettings || settings}
          onChange={handleChange}
          onSave={handleSave}
          onEdit={handleEdit}
          onCancel={handleCancel}
          editMode={editMode}
          loading={saving}
        />
      </div>
    </div>
  );
};

export default SettingsTab;
