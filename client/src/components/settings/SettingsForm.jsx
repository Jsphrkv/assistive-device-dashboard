import React from "react";
import { DISTANCE_THRESHOLDS, ALERT_MODE_OPTIONS } from "../../utils/constants";

const SettingsForm = ({ settings, onChange, userRole, onSave, loading }) => {
  const isUser = userRole === "user";

  return (
    <div className="space-y-6">
      {isUser && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>Limited Access:</strong> As a user, you can only modify
            sensitivity and alert mode settings.
          </p>
        </div>
      )}

      {/* Sensitivity */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Detection Sensitivity: {settings.sensitivity}%
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={settings.sensitivity}
          onChange={(e) => onChange("sensitivity", parseInt(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Distance Threshold */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Distance Threshold
        </label>
        <select
          value={settings.distanceThreshold}
          onChange={(e) =>
            onChange("distanceThreshold", parseInt(e.target.value))
          }
          disabled={isUser}
          className={`w-full px-3 py-2 border border-gray-300 rounded-lg ${
            isUser ? "bg-gray-100 cursor-not-allowed" : ""
          }`}
        >
          {DISTANCE_THRESHOLDS.map((threshold) => (
            <option key={threshold} value={threshold}>
              {threshold} cm
            </option>
          ))}
        </select>
      </div>

      {/* Alert Mode */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Alert Mode
        </label>
        <div className="space-y-2">
          {ALERT_MODE_OPTIONS.map((option) => (
            <label key={option.value} className="flex items-center">
              <input
                type="radio"
                name="alertMode"
                value={option.value}
                checked={settings.alertMode === option.value}
                onChange={(e) => onChange("alertMode", e.target.value)}
                className="mr-2"
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Sensor Controls */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-700">
          Enable / Disable Sensors
        </h3>

        <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-900">Ultrasonic Sensor</span>
          <input
            type="checkbox"
            checked={settings.ultrasonicEnabled}
            onChange={(e) => onChange("ultrasonicEnabled", e.target.checked)}
            disabled={isUser}
            className={isUser ? "cursor-not-allowed" : ""}
          />
        </label>

        <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-900">Camera Sensor</span>
          <input
            type="checkbox"
            checked={settings.cameraEnabled}
            onChange={(e) => onChange("cameraEnabled", e.target.checked)}
            disabled={isUser}
            className={isUser ? "cursor-not-allowed" : ""}
          />
        </label>
      </div>

      {/* Save Button */}
      <button
        onClick={onSave}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
      >
        {loading ? "Saving..." : "Save Settings"}
      </button>
    </div>
  );
};

export default SettingsForm;
