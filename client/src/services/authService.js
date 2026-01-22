import { authAPI } from "./api";
import { storage } from "../utils/helpers";

export const login = async (username, password) => {
  try {
    const response = await authAPI.login(username, password);
    const { token, user } = response.data;

    // Store token and user
    storage.set("token", token);
    storage.set("currentUser", user);

    return { user, error: null };
  } catch (error) {
    return {
      user: null,
      error: error.response?.data?.error || "Login failed",
    };
  }
};

export const logout = async () => {
  try {
    await authAPI.logout();
  } catch (error) {
    console.error("Logout error:", error);
  } finally {
    storage.remove("token");
    storage.remove("currentUser");
  }
  return { error: null };
};

export const getCurrentUser = () => {
  return storage.get("currentUser");
};

export const isAuthenticated = () => {
  return !!getCurrentUser() && !!storage.get("token");
};

export const isAdmin = () => {
  const user = getCurrentUser();
  return user?.role === "admin";
};

// Add logActivity function (used by SettingsTab)
export const logActivity = async (userId, action, description = null) => {
  // This will be handled by backend automatically
  // Just a placeholder for now
  console.log(`Activity: ${action}`, { userId, description });
};

export default {
  login,
  logout,
  getCurrentUser,
  isAuthenticated,
  isAdmin,
  logActivity,
};
