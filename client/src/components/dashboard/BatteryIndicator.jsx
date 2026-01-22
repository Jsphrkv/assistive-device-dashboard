import React from "react";
import { Battery } from "lucide-react";

const BatteryIndicator = ({ level }) => {
  const getColor = () => {
    if (level >= 70) return "bg-green-500";
    if (level >= 30) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getTextColor = () => {
    if (level >= 70) return "text-green-600";
    if (level >= 30) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">Battery Level</h3>
        <Battery className={`w-5 h-5 ${getTextColor()}`} />
      </div>
      <p className={`text-2xl font-bold ${getTextColor()}`}>{level}%</p>
      <div className="mt-2 bg-gray-200 rounded-full h-2">
        <div
          className={`${getColor()} h-2 rounded-full transition-all`}
          style={{ width: `${level}%` }}
        />
      </div>
    </div>
  );
};

export default BatteryIndicator;
