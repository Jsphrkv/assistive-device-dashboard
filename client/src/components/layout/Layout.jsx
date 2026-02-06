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
    <div className="min-h-screen bg-gray-50 px-4 py-4 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
      <Header currentUser={currentUser} onLogout={onLogout} />
      <Navigation activeTab={activeTab} onTabChange={onTabChange} />
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
};

export default Layout;
