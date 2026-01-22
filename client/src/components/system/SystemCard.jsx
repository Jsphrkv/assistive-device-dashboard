import React from "react";

const SystemCard = ({ label, value, color = "blue" }) => {
  const colorClasses = {
    blue: "border-blue-500",
    green: "border-green-500",
    yellow: "border-yellow-500",
    red: "border-red-500",
  };

  return (
    <div className={`border-l-4 ${colorClasses[color]} pl-4`}>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  );
};

export default SystemCard;
