import React from "react";
import { Activity, AlertTriangle, Camera, Settings, Info } from "lucide-react";

const Navigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "logs", label: "Detection Logs", icon: AlertTriangle },
    { id: "statistics", label: "Statistics", icon: Activity },
    { id: "camera", label: "Live Camera", icon: Camera },
    { id: "settings", label: "Settings", icon: Settings },
    // { id: "system", label: "System Info", icon: Info },
    { id: "devices", label: "Devices", icon: Info },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
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
  );
};

export default Navigation;
