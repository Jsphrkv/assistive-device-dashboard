import { useState, useEffect } from "react";
import { detectionsAPI } from "../services/api";

export const useDetectionLogs = (limit = 50, autoRefresh = false) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await detectionsAPI.getAll(limit, page * limit);
      setLogs(response.data.data);
      setTotalCount(response.data.count);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();

    if (autoRefresh) {
      const interval = setInterval(fetchLogs, 10000);
      return () => clearInterval(interval);
    }
  }, [page, limit, autoRefresh]);

  const nextPage = () => {
    const totalPages = Math.ceil(totalCount / limit);
    if (page < totalPages - 1) setPage(page + 1);
  };

  const prevPage = () => {
    if (page > 0) setPage(page - 1);
  };

  return {
    logs,
    loading,
    error,
    page,
    totalCount,
    totalPages: Math.ceil(totalCount / limit),
    nextPage,
    prevPage,
    refetch: fetchLogs,
  };
};

export default useDetectionLogs;
