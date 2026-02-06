import React from "react";
import {
  Activity,
  AlertTriangle,
  Camera,
  Settings,
  Info,
  Clock,
} from "lucide-react";

const Navigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "logs", label: "Detection Logs", icon: AlertTriangle },
    { id: "statistics", label: "Statistics", icon: Activity },
    { id: "mlhistory", label: "ML History", icon: Clock },
    { id: "camera", label: "Live Camera", icon: Camera },
    { id: "settings", label: "Settings", icon: Settings },
    { id: "device", label: "My Device", icon: Info },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 mb-4 sm:mb-6">
      <div className="max-w-7xl mx-auto">
        {/* Negative margin and padding trick to allow full-width scroll on mobile */}
        <div className="-mx-4 px-4 sm:mx-0 sm:px-0 overflow-x-auto nav-scroll">
          <div className="flex gap-1 sm:gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2.5 sm:py-3 border-b-2 transition-colors whitespace-nowrap text-sm sm:text-base flex-shrink-0 ${
                    activeTab === tab.id
                      ? "border-blue-600 text-blue-600 font-medium"
                      : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                  }`}
                >
                  <Icon className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
