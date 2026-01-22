import React, { useState, useEffect } from "react";
import LivePreview from "./LivePreview";
import config from "../../config";

const CameraTab = () => {
  const [frameCount, setFrameCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setFrameCount((prev) => prev + 1);
    }, config.camera.refreshInterval);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">Live Camera Preview</h2>

      <div className="bg-white rounded-lg shadow p-6">
        <LivePreview frameCount={frameCount} />
        <p className="text-sm text-gray-600 mt-4 text-center">
          Camera feed simulated with 3-5 second delay for processing
        </p>
      </div>
    </div>
  );
};

export default CameraTab;
