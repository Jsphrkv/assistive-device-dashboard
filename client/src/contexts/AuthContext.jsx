import React, { createContext, useContext, useState, useEffect } from "react";
import {
  getCurrentUser,
  login as loginService,
  logout as logoutService,
  isAuthenticated,
} from "../services/authService";
import { authAPI } from "../services/api";
import { storage } from "../utils/helpers"; // Make sure this import exists

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      console.log("🔍 Verifying auth on mount...");

      // Check if token exists
      if (!isAuthenticated()) {
        console.log("❌ No token found");
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        // Verify token is actually valid by calling backend
        console.log("✅ Token found, verifying with backend...");
        const response = await authAPI.getCurrentUser();
        console.log("✅ User verified:", response.data.user);
        setUser(response.data.user);
      } catch (error) {
        // Token is invalid/expired, clear everything
        console.error("❌ Auth verification failed:", error);
        storage.remove("token");
        storage.remove("currentUser");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifyAuth();
  }, []);

  const login = async (username, password) => {
    try {
      const { user, error } = await loginService(username, password);
      if (!error) {
        setUser(user);
      }
      return { user, error };
    } catch (error) {
      console.error("Login error:", error);
      return { user: null, error: error.message || "Login failed" };
    }
  };

  const logout = async () => {
    console.log("🔐 AuthContext logout called");

    try {
      await logoutService();
    } catch (error) {
      console.error("Logout service error:", error);
    } finally {
      // Always clear state and storage
      storage.remove("token");
      storage.remove("currentUser");
      setUser(null);
      console.log("✅ Storage cleared, user state reset");
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.role === "admin",
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export default AuthContext;
