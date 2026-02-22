import React from "react";
import { DISTANCE_THRESHOLDS, ALERT_MODE_OPTIONS } from "../../utils/constants";

const SettingsForm = ({
  settings,
  onChange,
  onSave,
  onEdit,
  onCancel,
  editMode,
  loading,
  isDirty, // FIX: receives dirty flag from parent to show unsaved changes warning
}) => {
  return (
    <div className="space-y-6">
      {/* FIX: Removed stale commented-out view mode banner — dead JSX
          comment blocks cause confusion about intended behaviour.
          If the banner is needed again, restore it from git history. */}

      {/* Unsaved changes warning */}
      {editMode && isDirty && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-sm text-amber-700">⚠️ You have unsaved changes.</p>
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
          disabled={!editMode}
          className={`w-full ${!editMode ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Low (fewer alerts)</span>
          <span>High (more alerts)</span>
        </div>
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
          disabled={!editMode}
          className={`w-full px-3 py-2 border border-gray-300 rounded-lg ${
            !editMode
              ? "bg-gray-100 opacity-60 cursor-not-allowed"
              : "focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          }`}
        >
          {DISTANCE_THRESHOLDS.map((threshold) => (
            <option key={threshold} value={threshold}>
              {threshold} cm
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-500 mt-1">
          Alert when obstacle is within this distance
        </p>
      </div>

      {/* Alert Mode */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Alert Mode
        </label>
        <div className="space-y-2">
          {ALERT_MODE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`flex items-center p-3 bg-gray-50 rounded-lg ${
                editMode
                  ? "cursor-pointer hover:bg-gray-100"
                  : "opacity-60 cursor-not-allowed"
              }`}
            >
              <input
                type="radio"
                name="alertMode"
                value={option.value}
                checked={settings.alertMode === option.value}
                onChange={(e) => onChange("alertMode", e.target.value)}
                disabled={!editMode}
                className="mr-3"
              />
              <span className="text-sm text-gray-900">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Sensor Controls */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-700">
          Enable / Disable Sensors
        </h3>

        <label
          className={`flex items-center justify-between p-3 bg-gray-50 rounded-lg ${
            editMode
              ? "cursor-pointer hover:bg-gray-100"
              : "opacity-60 cursor-not-allowed"
          }`}
        >
          <div>
            <span className="text-sm font-medium text-gray-900">
              Ultrasonic Sensor
            </span>
            <p className="text-xs text-gray-500">
              Close-range obstacle detection (0-3.5m)
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.ultrasonicEnabled}
            onChange={(e) => onChange("ultrasonicEnabled", e.target.checked)}
            disabled={!editMode}
            className={`w-4 h-4 ${editMode ? "cursor-pointer" : "cursor-not-allowed"}`}
          />
        </label>

        <label
          className={`flex items-center justify-between p-3 bg-gray-50 rounded-lg ${
            editMode
              ? "cursor-pointer hover:bg-gray-100"
              : "opacity-60 cursor-not-allowed"
          }`}
        >
          <div>
            <span className="text-sm font-medium text-gray-900">
              Camera Sensor
            </span>
            <p className="text-xs text-gray-500">
              Far-range detection (3.5-20m)
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.cameraEnabled}
            onChange={(e) => onChange("cameraEnabled", e.target.checked)}
            disabled={!editMode}
            className={`w-4 h-4 ${editMode ? "cursor-pointer" : "cursor-not-allowed"}`}
          />
        </label>
      </div>

      {/* Buttons */}
      {!editMode ? (
        <button
          onClick={onEdit}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          ✏️ Edit Settings
        </button>
      ) : (
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-lg hover:bg-gray-200 transition-colors font-medium disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
          >
            {loading ? "Saving..." : "💾 Save Settings"}
          </button>
        </div>
      )}
    </div>
  );
};

export default SettingsForm;
