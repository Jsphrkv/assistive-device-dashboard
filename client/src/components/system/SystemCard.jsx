import React from "react";

const SystemCard = ({ label, value, color = "blue" }) => {
  // FIX: Added missing "gray" color — was used in DeviceSystemTab but
  // absent here, causing those cards to render with no left border.
  const colorClasses = {
    blue: "border-blue-500",
    green: "border-green-500",
    yellow: "border-yellow-500",
    red: "border-red-500",
    gray: "border-gray-400",
  };

  return (
    <div
      className={`border-l-4 ${colorClasses[color] ?? "border-gray-400"} pl-4`}
    >
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  );
};

export default SystemCard;
