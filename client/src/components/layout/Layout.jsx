import React from "react";
import Header from "./Header";
import Navigation from "./Navigation";

const Layout = ({
  currentUser,
  activeTab,
  onTabChange,
  onLogout,
  children,
}) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentUser={currentUser} onLogout={onLogout} />
      {/* FIX: Pass currentUser so Navigation can render role-appropriate tabs */}
      <Navigation
        currentUser={currentUser}
        activeTab={activeTab}
        onTabChange={onTabChange}
      />
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
};

export default Layout;
