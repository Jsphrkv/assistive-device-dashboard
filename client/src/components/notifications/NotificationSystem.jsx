import React, { useState, useEffect } from "react";
import { X, AlertTriangle, CheckCircle, Info, AlertCircle } from "lucide-react";

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Listen for ML events
    const interval = setInterval(checkForAlerts, 15000);
    return () => clearInterval(interval);
  }, []);

  const checkForAlerts = async () => {
    try {
      // Simulated check - replace with real ML API calls
      const shouldAlert = Math.random() > 0.7;

      if (shouldAlert) {
        const alertTypes = [
          {
            type: "anomaly",
            title: "Anomaly Detected",
            message: "High anomaly score detected on Device-001",
            severity: "warning",
            icon: AlertTriangle,
          },
          {
            type: "maintenance",
            title: "Maintenance Required",
            message: "Device battery replacement recommended",
            severity: "info",
            icon: Info,
          },
          {
            type: "activity",
            title: "Activity Alert",
            message: "Unusual activity pattern detected",
            severity: "error",
            icon: AlertCircle,
          },
        ];

        const randomAlert =
          alertTypes[Math.floor(Math.random() * alertTypes.length)];
        addNotification(randomAlert);
      }
    } catch (error) {
      console.error("Error checking alerts:", error);
    }
  };

  const addNotification = (notification) => {
    const id = Date.now();
    const newNotification = { ...notification, id, timestamp: new Date() };

    setNotifications((prev) => [newNotification, ...prev]);

    // Auto-remove after 10 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 10000);
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
    <div className="fixed top-20 right-4 z-50 space-y-3 max-w-sm">
      {notifications.map((notification) => {
        const Icon = notification.icon;
        return (
          <div
            key={notification.id}
            className={`rounded-lg border-l-4 p-4 shadow-lg animate-slide-in ${getSeverityStyles(notification.severity)}`}
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
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default NotificationSystem;
