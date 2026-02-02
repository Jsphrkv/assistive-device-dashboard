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
import DeviceSystemTab from "./components/system/DeviceSystemTab";
import HistoricalDataTab from "./components/ml/HistoricalDataTab";
import { MLHistoryProvideruse } from "./contexts/MLHistoryContext.jsx";
import { useAuth } from "./contexts/AuthContext";
import NotificationSystem from "./components/notifications/NotificationSystem";

function App() {
  const { user: authUser, loading, logout } = useAuth(); // ✅ Get logout from useAuth
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [currentView, setCurrentView] = useState("login");

  // Sync currentUser with AuthContext
  useEffect(() => {
    console.log("🔄 Syncing user from AuthContext:", authUser);
    setCurrentUser(authUser);
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
    setCurrentView("login");
    window.history.pushState({}, "", "/");
  };

  // ✅ FIXED: Now calls AuthContext logout to clear storage
  const handleLogout = async () => {
    console.log("🚪 Logout initiated from App.jsx");

    // Call the actual logout from AuthContext (clears storage)
    await logout();

    // Clear local state
    setCurrentUser(null);
    setActiveTab("dashboard");
    setCurrentView("login");

    // Update URL
    window.history.pushState({}, "", "/");

    console.log("✅ Logout complete");
  };

  const handleShowRegister = () => setCurrentView("register");
  const handleShowLogin = () => {
    setCurrentView("login");
    window.history.pushState({}, "", "/");
  };
  const handleShowForgotPassword = () => setCurrentView("forgotPassword");

  // Show loading state while checking auth
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

  // Logged in - show dashboard
  const renderActiveTab = () => {
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
      // case "devices":
      //   return <DevicesTab />;
      default:
        return <DashboardTab />;
    }
  };

  return (
    <MLHistoryProvider>
      <Layout
        currentUser={currentUser}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onLogout={handleLogout}
      >
        <NotificationSystem />
        {renderActiveTab()}
      </Layout>
    </MLHistoryProvider>
  );
}

export default App;
