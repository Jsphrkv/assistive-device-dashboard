import React, { useState, useEffect } from "react";
import {
  X,
  AlertTriangle,
  Info,
  AlertCircle,
  Battery,
  Camera,
  Activity,
} from "lucide-react";
import { storage } from "../../utils/helpers";

// Import API_BASE_URL - matches your api.js configuration
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "https://assistive-device-dashboard.onrender.com/api";

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);
  const [shownNotifications, setShownNotifications] = useState(new Set());

  useEffect(() => {
    // Check for ML anomalies every 5 seconds
    const anomalyInterval = setInterval(checkForAnomalies, 5000);

    // Check device status every 30 seconds
    const statusInterval = setInterval(checkDeviceStatus, 30000);

    // Initial checks
    checkForAnomalies();
    checkDeviceStatus();

    return () => {
      clearInterval(anomalyInterval);
      clearInterval(statusInterval);
    };
  }, []);

  const checkForAnomalies = async () => {
    try {
      // Use storage.get() to match your api.js
      const token = storage.get("token");
      if (!token) return;

      // Note: API_BASE_URL already includes /api, so just add the endpoint path
      const response = await fetch(
        `${API_BASE_URL}/ml-history/anomalies?limit=10`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        console.log("Anomalies check failed:", response.status);
        return;
      }

      const result = await response.json();
      const anomalies = result.data || [];

      // Process only new anomalies
      anomalies.forEach((anomaly) => {
        const notificationKey = `${anomaly.source}-${anomaly.id}`;

        // Skip if already shown
        if (shownNotifications.has(notificationKey)) return;

        // Only notify for high severity or critical
        if (shouldNotify(anomaly)) {
          addNotification({
            type: anomaly.type,
            title: getNotificationTitle(anomaly),
            message: anomaly.message,
            severity: mapSeverity(anomaly.severity),
            icon: getIcon(anomaly.type),
            anomalyId: anomaly.id,
            source: anomaly.source,
          });

          // Mark as shown
          setShownNotifications((prev) => new Set(prev).add(notificationKey));
        }
      });
    } catch (error) {
      console.error("Error checking anomalies:", error);
    }
  };

  const checkDeviceStatus = async () => {
    try {
      // Use storage.get() to match your api.js
      const token = storage.get("token");
      if (!token) return;

      // Note: API_BASE_URL already includes /api
      const response = await fetch(`${API_BASE_URL}/devices/status`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.log("Device status check failed:", response.status);
        return;
      }

      const status = await response.json();

      // Check battery level (warn if below 20%)
      if (status.batteryLevel !== null && status.batteryLevel < 20) {
        const batteryKey = `battery-${Math.floor(status.batteryLevel / 5)}`; // Group by 5% increments

        if (!shownNotifications.has(batteryKey)) {
          addNotification({
            type: "battery",
            title: "🔋 Low Battery Warning",
            message: `Device battery at ${status.batteryLevel}%. Please charge soon.`,
            severity: status.batteryLevel < 10 ? "error" : "warning",
            icon: Battery,
          });

          setShownNotifications((prev) => new Set(prev).add(batteryKey));
        }
      }

      // Check camera status
      if (
        status.cameraStatus === "offline" ||
        status.cameraStatus === "error"
      ) {
        const cameraKey = `camera-${status.cameraStatus}`;

        if (!shownNotifications.has(cameraKey)) {
          addNotification({
            type: "camera",
            title: "📷 Camera Issue",
            message: `Camera is ${status.cameraStatus}. Please check device.`,
            severity: "error",
            icon: Camera,
          });

          setShownNotifications((prev) => new Set(prev).add(cameraKey));
        }
      }

      // Check if device is offline
      if (status.hasDevice && !status.deviceOnline) {
        const offlineKey = "device-offline";

        if (!shownNotifications.has(offlineKey)) {
          addNotification({
            type: "device",
            title: "⚠️ Device Offline",
            message:
              "Your assistive device is offline. Please check connection.",
            severity: "warning",
            icon: AlertTriangle,
          });

          setShownNotifications((prev) => new Set(prev).add(offlineKey));
        }
      }
    } catch (error) {
      console.error("Error checking device status:", error);
    }
  };

  const shouldNotify = (anomaly) => {
    // For ML predictions: only high/critical severity
    if (anomaly.source === "ml_prediction") {
      return ["high", "critical"].includes(anomaly.severity?.toLowerCase());
    }

    // For detections: only High/Critical danger levels
    if (anomaly.source === "detection_log") {
      return ["high", "critical"].includes(anomaly.severity?.toLowerCase());
    }

    return false;
  };

  const getNotificationTitle = (anomaly) => {
    if (anomaly.type === "detection") {
      // Extract obstacle type from message if available
      const obstacleMatch = anomaly.message?.match(/(\w+)\s+detected/i);
      const obstacleType = obstacleMatch ? obstacleMatch[1] : "Obstacle";
      return `⚠️ ${obstacleType} Detected!`;
    }

    if (anomaly.type === "anomaly") {
      return "🔍 Anomaly Detected";
    }

    if (anomaly.type === "maintenance") {
      return "🔧 Maintenance Alert";
    }

    if (anomaly.type === "activity") {
      return "🏃 Activity Alert";
    }

    return "⚠️ Alert";
  };

  const getIcon = (type) => {
    switch (type) {
      case "detection":
        return AlertTriangle;
      case "anomaly":
        return AlertCircle;
      case "maintenance":
        return Info;
      case "activity":
        return Activity;
      case "battery":
        return Battery;
      case "camera":
        return Camera;
      case "device":
        return AlertTriangle;
      default:
        return AlertCircle;
    }
  };

  const mapSeverity = (severity) => {
    const severityLower = severity?.toLowerCase() || "info";

    if (["critical", "high"].includes(severityLower)) return "error";
    if (severityLower === "medium") return "warning";
    return "info";
  };

  const addNotification = (notification) => {
    const id = Date.now() + Math.random();
    const newNotification = { ...notification, id, timestamp: new Date() };

    setNotifications((prev) => {
      // Limit to 5 notifications at a time
      const updated = [newNotification, ...prev].slice(0, 5);
      return updated;
    });

    // Auto-remove timing based on type
    let timeout = 15000; // Default: 15 seconds

    if (["detection", "anomaly"].includes(notification.type)) {
      timeout = 15000; // 15 seconds for urgent alerts
    } else if (["maintenance", "device"].includes(notification.type)) {
      timeout = 30000; // 30 seconds for maintenance/device issues
    } else if (["battery", "camera"].includes(notification.type)) {
      timeout = 45000; // 45 seconds for hardware issues
    }

    setTimeout(() => {
      removeNotification(id);
    }, timeout);
  };

  const removeNotification = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const getSeverityStyles = (severity) => {
    switch (severity) {
      case "error":
        return "bg-red-50 border-red-500 text-red-900";
      case "warning":
        return "bg-yellow-50 border-yellow-500 text-yellow-900";
      case "info":
        return "bg-blue-50 border-blue-500 text-blue-900";
      case "success":
        return "bg-green-50 border-green-500 text-green-900";
      default:
        return "bg-gray-50 border-gray-500 text-gray-900";
    }
  };

  if (notifications.length === 0) return null;

  return (
    <>
      <div className="fixed top-20 right-4 z-50 space-y-3 max-w-sm">
        {notifications.map((notification) => {
          const Icon = notification.icon;
          return (
            <div
              key={notification.id}
              className={`rounded-lg border-l-4 p-4 shadow-lg transition-all duration-300 ease-in-out ${getSeverityStyles(
                notification.severity,
              )}`}
              style={{
                animation: "slideIn 0.3s ease-out",
              }}
            >
              <div className="flex items-start">
                <Icon className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">
                    {notification.title}
                  </h4>
                  <p className="text-xs opacity-90">{notification.message}</p>
                  <p className="text-xs opacity-75 mt-1">
                    {notification.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                <button
                  onClick={() => removeNotification(notification.id)}
                  className="ml-2 hover:opacity-70 transition-opacity"
                  aria-label="Dismiss notification"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
};

export default NotificationSystem;
