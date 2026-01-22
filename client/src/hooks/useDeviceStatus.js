import { useState, useEffect } from "react";
import { deviceAPI } from "../services/api";
import { REFRESH_INTERVALS } from "../utils/constants";

export const useDeviceStatus = (autoRefresh = true) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      const response = await deviceAPI.getStatus();
      setStatus(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    if (autoRefresh) {
      const interval = setInterval(
        fetchStatus,
        REFRESH_INTERVALS.DEVICE_STATUS,
      );
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  return { status, loading, error, refetch: fetchStatus };
};

export default useDeviceStatus;
