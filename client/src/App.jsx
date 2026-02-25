import React, { useState, useEffect } from "react";
import LoginForm from "./pages/LoginForm";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmail from "./pages/VerifyEmail";
import Layout from "./components/layout/Layout";

// Regular user tabs
import DashboardTab from "./components/dashboard/DashboardTab";
import DetectionLogsTab from "./components/logs/DetectionLogsTab";
import StatisticsTab from "./components/statistics/StatisticsTab";
import CameraTab from "./components/camera/CameraTab";
import SettingsTab from "./components/settings/SettingsTab";
import DeviceSystemTab from "./components/system/DeviceSystemTab";
import HistoricalDataTab from "./components/ml/HistoricalDataTab";

// Admin-only tabs
import AdminSystemHealth from "./components/admin/AdminSystemHealth";
import AdminDetectionLogs from "./components/admin/AdminDetectionLogs";
import AdminMLAnalytics from "./components/admin/AdminMLAnalytics";
import AdminUserManagement from "./components/admin/AdminUserManagement";
import AdminLiveFeed from "./components/admin/AdminLiveFeed";

import { useAuth } from "./contexts/AuthContext";

function App() {
  const { user: authUser, loading, logout } = useAuth();
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState(null); // null until user role is known
  const [currentView, setCurrentView] = useState("login");

  // Sync currentUser with AuthContext
  useEffect(() => {
    console.log("🔄 Syncing user from AuthContext:", authUser);
    setCurrentUser(authUser);

    // Set the correct default tab based on role when user changes
    if (authUser) {
      const defaultTab =
        authUser.role === "admin" ? "admin-health" : "dashboard";
      setActiveTab((prev) => prev ?? defaultTab);
    }
  }, [authUser]);

  useEffect(() => {
    const path = window.location.pathname;
    const search = window.location.search;

    console.log("=".repeat(60));
    console.log("APP ROUTING");
    console.log("Path:", path);
    console.log("Search:", search);

    if (path === "/reset-password" && search.includes("token=")) {
      console.log("→ Route: PASSWORD RESET");
      setCurrentView("resetPassword");
    } else if (path === "/verify-email" && search.includes("token=")) {
      console.log("→ Route: EMAIL VERIFICATION");
      setCurrentView("verifyEmail");
    } else {
      console.log("→ Route: DEFAULT");
    }
    console.log("=".repeat(60));
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
    // Set correct default tab immediately on login
    setActiveTab(user.role === "admin" ? "admin-health" : "dashboard");
    setCurrentView("login");
    window.history.pushState({}, "", "/");
  };

  const handleLogout = async () => {
    console.log("🚪 Logout initiated from App.jsx");
    await logout();
    setCurrentUser(null);
    setActiveTab(null);
    setCurrentView("login");
    window.history.pushState({}, "", "/");
    console.log("✅ Logout complete");
  };

  const handleShowRegister = () => setCurrentView("register");
  const handleShowLogin = () => {
    setCurrentView("login");
    window.history.pushState({}, "", "/");
  };
  const handleShowForgotPassword = () => setCurrentView("forgotPassword");

  const handleTabChange = (tabId) => {
    // Guard: admin can only access admin tabs, users can only access user tabs
    const isAdmin = currentUser?.role === "admin";
    const isAdminTab = tabId.startsWith("admin-");
    if (isAdmin !== isAdminTab) return; // silently block cross-role navigation
    setActiveTab(tabId);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (currentView === "verifyEmail") {
    return <VerifyEmail onShowLogin={handleShowLogin} />;
  }

  if (currentView === "resetPassword") {
    return <ResetPassword onShowLogin={handleShowLogin} />;
  }

  if (!currentUser) {
    if (currentView === "register") {
      return <Register onShowLogin={handleShowLogin} />;
    }
    if (currentView === "forgotPassword") {
      return <ForgotPassword onShowLogin={handleShowLogin} />;
    }
    return (
      <LoginForm
        onLogin={handleLogin}
        onShowRegister={handleShowRegister}
        onShowForgotPassword={handleShowForgotPassword}
      />
    );
  }

  const isAdmin = currentUser.role === "admin";

  // ── Tab renderer ──────────────────────────────────────────────────────────
  const renderActiveTab = () => {
    // Admin routes
    if (isAdmin) {
      switch (activeTab) {
        case "admin-health":
          return <AdminSystemHealth />;
        case "admin-logs":
          return <AdminDetectionLogs />;
        case "admin-analytics":
          return <AdminMLAnalytics />;
        case "admin-users":
          return <AdminUserManagement />;
        case "admin-feed":
          return <AdminLiveFeed />;
        default:
          return <AdminSystemHealth />;
      }
    }

    // Regular user routes — unchanged
    switch (activeTab) {
      case "dashboard":
        return <DashboardTab />;
      case "logs":
        return <DetectionLogsTab />;
      case "statistics":
        return <StatisticsTab />;
      case "mlhistory":
        return <HistoricalDataTab />;
      case "camera":
        return <CameraTab />;
      case "settings":
        return <SettingsTab currentUser={currentUser} />;
      case "device":
        return <DeviceSystemTab />;
      default:
        return <DashboardTab />;
    }
  };

  return (
    <Layout
      currentUser={currentUser}
      activeTab={activeTab || (isAdmin ? "admin-health" : "dashboard")}
      onTabChange={handleTabChange}
      onLogout={handleLogout}
    >
      {renderActiveTab()}
    </Layout>
  );
}

export default App;
