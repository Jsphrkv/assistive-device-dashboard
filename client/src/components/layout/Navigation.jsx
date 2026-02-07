import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  Camera,
  Settings,
  Info,
  Clock,
  Menu,
  X,
} from "lucide-react";

const Navigation = ({ activeTab, onTabChange }) => {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Match your App.jsx tab structure
  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "logs", label: "Detection Logs", icon: AlertTriangle },
    { id: "statistics", label: "Statistics", icon: Activity },
    { id: "mlhistory", label: "ML History", icon: Clock },
    { id: "camera", label: "Live Camera", icon: Camera },
    { id: "settings", label: "Settings", icon: Settings },
    { id: "device", label: "My Device", icon: Info },
  ];

  // Check screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setIsMobileNavOpen(false);
      }
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleTabChange = (tabId) => {
    onTabChange(tabId);
    setIsMobileNavOpen(false);
  };

  return (
    <>
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          {/* Mobile: Burger + Active Tab */}
          <div className="md:hidden flex items-center justify-between py-3">
            <button
              onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
              className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isMobileNavOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
              <span className="font-medium">Menu</span>
            </button>

            {/* Current Active Tab Display */}
            <div className="flex items-center gap-2 text-blue-600 font-medium">
              {React.createElement(
                tabs.find((t) => t.id === activeTab)?.icon || Activity,
                { className: "w-4 h-4" },
              )}
              <span className="text-sm">
                {tabs.find((t) => t.id === activeTab)?.label}
              </span>
            </div>
          </div>

          {/* Desktop: Horizontal Tabs */}
          <div className="hidden md:flex gap-1 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all whitespace-nowrap ${
                    activeTab === tab.id
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-600 hover:text-gray-900"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Mobile: Slide-in Menu */}
      {isMobile && (
        <>
          {/* Overlay */}
          <div
            className={`fixed inset-0 bg-black transition-opacity duration-300 z-40 ${
              isMobileNavOpen
                ? "opacity-50 pointer-events-auto"
                : "opacity-0 pointer-events-none"
            }`}
            onClick={() => setIsMobileNavOpen(false)}
          />

          {/* Slide-in Navigation */}
          <div
            className={`fixed top-0 left-0 h-full w-72 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 ${
              isMobileNavOpen ? "translate-x-0" : "-translate-x-full"
            }`}
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-gray-900">Menu</h2>
                <button
                  onClick={() => setIsMobileNavOpen(false)}
                  className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Navigation Links */}
              <div className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => handleTabChange(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                        activeTab === tab.id
                          ? "bg-blue-600 text-white shadow-md"
                          : "text-gray-700 hover:bg-gray-100"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default Navigation;
