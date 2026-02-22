import React, { useState, useEffect, useRef } from "react";
import SettingsForm from "./SettingsForm";
import { settingsAPI } from "../../services/api";

const APPLY_DELAY_SECONDS = 30;

const SettingsTab = () => {
  const defaultSettings = {
    sensitivity: 75,
    distanceThreshold: 100,
    alertMode: "both",
    ultrasonicEnabled: true,
    cameraEnabled: true,
  };

  const [settings, setSettings] = useState(defaultSettings);
  const [pendingSettings, setPendingSettings] = useState(defaultSettings);
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [countdown, setCountdown] = useState(null);

  // FIX: Added fetchError so a failed initial load is visible to the user
  // instead of silently falling back to default values with no indication
  // that the real settings couldn't be retrieved.
  const [fetchError, setFetchError] = useState(false);

  const countdownRef = useRef(null);

  const isDirty =
    editMode && JSON.stringify(pendingSettings) !== JSON.stringify(settings);

  useEffect(() => {
    fetchSettings();
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setFetchError(false);
    try {
      const response = await settingsAPI.get();
      if (response.data?.data) {
        const fetched = response.data.data;
        setSettings(fetched);
        if (!editMode) {
          setPendingSettings(fetched);
        }
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
      // FIX: Surface the error — user now sees a banner with a Retry
      // button instead of silently seeing defaults as if they were real.
      setFetchError(true);
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">
        Settings & Configuration
      </h2>

      {/* FIX: Fetch error banner with Retry button */}
      {fetchError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-red-800">
              ⚠️ Could not load your settings
            </p>
            <p className="text-xs text-red-700 mt-1">
              Showing default values. Your saved settings couldn't be retrieved
              — changes you make now will overwrite whatever is stored.
            </p>
          </div>
          <button
            onClick={fetchSettings}
            className="flex-shrink-0 px-3 py-1.5 text-xs font-medium bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Inline message banner */}
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

      {/* Countdown banner */}
      {countdown !== null && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-amber-800">
                ⏳ Settings saved — applying to device...
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
                width: `${
                  ((APPLY_DELAY_SECONDS - countdown) / APPLY_DELAY_SECONDS) *
                  100
                }%`,
              }}
            />
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <SettingsForm
          settings={pendingSettings}
          onChange={handleChange}
          onSave={handleSave}
          onEdit={handleEdit}
          onCancel={handleCancel}
          editMode={editMode}
          loading={saving}
          isDirty={isDirty}
        />
      </div>
    </div>
  );
};

export default SettingsTab;
