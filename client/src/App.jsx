import React, { useState, useEffect } from "react";
import LoginForm from "./pages/LoginForm";
import Register from "./pages/Register";
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
  const [showRegister, setShowRegister] = useState(false); // NEW: Track if showing register page

  useEffect(() => {
    // Check if user is already logged in
    const user = getCurrentUser();
    if (user) {
      setCurrentUser(user);
    }
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
    setShowRegister(false); // Reset to login view
  };

  const handleLogout = () => {
    // Clear localStorage first
    localStorage.removeItem("token");
    localStorage.removeItem("currentUser");

    // Then update state
    setCurrentUser(null);
    setActiveTab("dashboard");
    setShowRegister(false);
  };

  const handleShowRegister = () => {
    setShowRegister(true);
  };

  const handleShowLogin = () => {
    setShowRegister(false);
  };

  // If not logged in, show login or register page
  if (!currentUser) {
    if (showRegister) {
      return <Register onShowLogin={handleShowLogin} />;
    }
    return (
      <LoginForm onLogin={handleLogin} onShowRegister={handleShowRegister} />
    );
  }

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
