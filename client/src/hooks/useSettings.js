import { useState, useEffect } from "react";
import {
  getUserSettings,
  updateUserSettings,
} from "../services/settingsService";

export const useSettings = (userId, userRole) => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.getSettings();
      // ✅ Handle both formats
      const settingsData = response.data?.data || response.data;
      if (settingsData) {
        setSettings(settingsData);
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
      // ✅ Show error to user
      setMessage("Failed to load settings. Using defaults.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchSettings();
    }
  }, [userId]);

  const updateSettings = async (newSettings) => {
    try {
      setSaving(true);
      const { error } = await updateUserSettings(userId, newSettings, userRole);

      if (error) {
        setError(error);
        return { success: false, error };
      } else {
        setSettings({ ...settings, ...newSettings });
        setError(null);
        return { success: true, error: null };
      }
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setSaving(false);
    }
  };

  return {
    settings,
    loading,
    saving,
    error,
    updateSettings,
    refetch: fetchSettings,
  };
};

export default useSettings;
