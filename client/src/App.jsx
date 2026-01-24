import React, { useState, useEffect } from "react";
import LoginForm from "./pages/LoginForm";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmail from "./pages/VerifyEmail";
import Layout from "./components/layout/Layout";
import DashboardTab from "./components/dashboard/DashboardTab";
import DetectionLogsTab from "./components/logs/DetectionLogsTab";
import StatisticsTab from "./components/statistics/StatisticsTab";
import CameraTab from "./components/camera/CameraTab";
import SettingsTab from "./components/settings/SettingsTab";
import SystemInfoTab from "./components/system/SystemInfoTab";
import DevicesTab from "./components/devices/DevicesTab";
import { getCurrentUser } from "./services/authService";

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [currentView, setCurrentView] = useState("login"); // login, register, forgotPassword, resetPassword, verifyEmail

  useEffect(() => {
    // Check URL for special routes
    const path = window.location.pathname;
    const search = window.location.search;

    console.log("=".repeat(60));
    console.log("APP ROUTING");
    console.log("Path:", path);
    console.log("Search:", search);

    // Check for password reset FIRST (more specific)
    if (path === "/reset-password" && search.includes("token=")) {
      console.log("→ Route: PASSWORD RESET");
      setCurrentView("resetPassword");
    }
    // Then check for email verification
    else if (path === "/verify-email" && search.includes("token=")) {
      console.log("→ Route: EMAIL VERIFICATION");
      setCurrentView("verifyEmail");
    }
    // Default: check if user is logged in
    else {
      console.log("→ Route: DEFAULT (checking auth)");
      const user = getCurrentUser();
      if (user) {
        setCurrentUser(user);
      }
    }
    console.log("=".repeat(60));
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
    setCurrentView("login");
    // Clear URL params
    window.history.pushState({}, "", "/");
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setActiveTab("dashboard");
    setCurrentView("login");
    window.history.pushState({}, "", "/");
  };

  const handleShowRegister = () => setCurrentView("register");
  const handleShowLogin = () => {
    setCurrentView("login");
    window.history.pushState({}, "", "/");
  };
  const handleShowForgotPassword = () => setCurrentView("forgotPassword");

  // Handle special views (email verification, password reset)
  if (currentView === "verifyEmail") {
    return <VerifyEmail onShowLogin={handleShowLogin} />;
  }

  if (currentView === "resetPassword") {
    return <ResetPassword onShowLogin={handleShowLogin} />;
  }

  // Not logged in - show auth views
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

  // Logged in - show dashboard
  const renderActiveTab = () => {
    switch (activeTab) {
      case "dashboard":
        return <DashboardTab />;
      case "logs":
        return <DetectionLogsTab />;
      case "statistics":
        return <StatisticsTab />;
      case "camera":
        return <CameraTab />;
      case "settings":
        return <SettingsTab currentUser={currentUser} />;
      case "system":
        return <SystemInfoTab />;
      case "devices":
        return <DevicesTab />;
      default:
        return <DashboardTab />;
    }
  };

  return (
    <Layout
      currentUser={currentUser}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      onLogout={handleLogout}
    >
      {renderActiveTab()}
    </Layout>
  );
}

export default App;
