import React, { createContext, useContext, useState, useEffect } from "react";
import {
  getCurrentUser,
  login as loginService,
  logout as logoutService,
  isAuthenticated,
} from "../services/authService";
// import { useNavigate } from "react-router-dom";
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

        // Clear storage synchronously
        storage.remove("token");
        storage.remove("currentUser");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifyAuth();
  }, []);

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
