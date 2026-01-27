import React, { createContext, useContext, useState, useEffect } from "react";
import {
  getCurrentUser,
  login as loginService,
  logout as logoutService,
  isAuthenticated,
} from "../services/authService";
import { authAPI } from "../services/api"; // Add this import

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      // Check if token exists
      if (!isAuthenticated()) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        // Verify token is actually valid by calling backend
        const response = await authAPI.getCurrentUser();
        setUser(response.data.user);
      } catch (error) {
        // Token is invalid/expired, clear everything
        console.error("Auth verification failed:", error);
        await logoutService(); // This clears storage
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifyAuth();
  }, []);

  const login = async (username, password) => {
    const { user, error } = await loginService(username, password);
    if (!error) {
      setUser(user);
    }
    return { user, error };
  };

  const logout = async () => {
    await logoutService();
    setUser(null);
    // Force redirect to login page
    window.location.href = "/";
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
