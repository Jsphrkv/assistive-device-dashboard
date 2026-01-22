import React from "react";

const Card = ({ children, className = "", title, icon: Icon }) => {
  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {(title || Icon) && (
        <div className="flex items-center justify-between mb-4">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          )}
          {Icon && <Icon className="w-5 h-5 text-gray-500" />}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
