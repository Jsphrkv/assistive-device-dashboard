import React from "react";
import { LogOut } from "lucide-react";

const Header = ({ currentUser, onLogout }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Assistive Device Dashboard
          </h1>
          <p className="text-sm text-gray-600">
            Computer Vision Obstacle Detection System
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">
              {currentUser.username}
            </p>
            <p className="text-xs text-gray-500 capitalize">
              {currentUser.role}
            </p>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
