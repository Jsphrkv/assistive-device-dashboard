import React from "react";
import { Camera } from "lucide-react";

const LivePreview = ({ frameCount }) => {
  return (
    <div className="bg-gray-900 rounded-lg aspect-video flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center">
        <Camera className="w-24 h-24 text-gray-700" />
      </div>

      <div className="absolute top-4 left-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm flex items-center gap-2">
        <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
        LIVE
      </div>

      <div className="absolute bottom-4 right-4 bg-black bg-opacity-75 text-white px-3 py-1 rounded text-sm">
        3-5 sec delay • Frame: {frameCount}
      </div>

      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10" />
    </div>
  );
};

export default LivePreview;
