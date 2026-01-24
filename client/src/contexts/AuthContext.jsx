import React, { createContext, useContext, useState, useEffect } from "react";
import {
  getCurrentUser,
  login as loginService,
  logout as logoutService,
  isAuthenticated,
} from "../services/authService";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Only set user if they're actually authenticated (token exists)
    if (isAuthenticated()) {
      const currentUser = getCurrentUser();
      setUser(currentUser);
    } else {
      setUser(null);
    }
    setLoading(false);
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
