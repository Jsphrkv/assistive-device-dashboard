import { format, formatDistanceToNow } from "date-fns";

/**
 * Format date to readable string
 */
export const formatDate = (date, formatStr = "yyyy-MM-dd HH:mm:ss") => {
  if (!date) return "-";
  return format(new Date(date), formatStr);
};

/**
 * Format relative time (e.g., "2 mins ago")
 */
export const formatRelativeTime = (date) => {
  if (!date) return "-";
  return formatDistanceToNow(new Date(date), { addSuffix: true });
};

/**
 * Get danger level color
 */
export const getDangerColor = (level) => {
  const colors = {
    Low: "bg-green-100 text-green-800",
    Medium: "bg-yellow-100 text-yellow-800",
    High: "bg-red-100 text-red-800",
  };
  return colors[level] || "bg-gray-100 text-gray-800";
};

/**
 * Get battery level color
 */
export const getBatteryColor = (level) => {
  if (level >= 70) return "text-green-600";
  if (level >= 30) return "text-yellow-600";
  return "text-red-600";
};

/**
 * Check if user is admin
 */
export const isAdmin = (user) => {
  return user?.role === "admin";
};

/**
 * Truncate text
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text || text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Debounce function
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Format distance with unit
 */
export const formatDistance = (distance, unit = "cm") => {
  if (distance === null || distance === undefined) return "-";
  return `${distance} ${unit}`;
};

/**
 * Calculate percentage
 */
export const calculatePercentage = (value, total) => {
  if (!total) return 0;
  return Math.round((value / total) * 100);
};

/**
 * Sort array by property
 */
export const sortBy = (array, property, order = "asc") => {
  const sorted = [...array].sort((a, b) => {
    if (a[property] < b[property]) return order === "asc" ? -1 : 1;
    if (a[property] > b[property]) return order === "asc" ? 1 : -1;
    return 0;
  });
  return sorted;
};

/**
 * Group array by property
 */
export const groupBy = (array, property) => {
  return array.reduce((acc, obj) => {
    const key = obj[property];
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(obj);
    return acc;
  }, {});
};

/**
 * Generate random color
 */
export const generateColor = () => {
  return "#" + Math.floor(Math.random() * 16777215).toString(16);
};

/**
 * Validate email
 */
export const isValidEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};

/**
 * Local storage helpers
 */
export const storage = {
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error("Storage set error:", error);
    }
  },

  get: (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error("Storage get error:", error);
      return null;
    }
  },

  remove: (key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error("Storage remove error:", error);
    }
  },

  clear: () => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error("Storage clear error:", error);
    }
  },
};

export default {
  formatDate,
  formatRelativeTime,
  getDangerColor,
  getBatteryColor,
  isAdmin,
  truncateText,
  debounce,
  formatDistance,
  calculatePercentage,
  sortBy,
  groupBy,
  generateColor,
  isValidEmail,
  storage,
};
