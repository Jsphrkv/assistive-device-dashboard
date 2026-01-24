import React, { useState, useEffect } from "react";
import { authAPI } from "../services/api";
import { CheckCircle, XCircle, Loader } from "lucide-react";

const VerifyEmail = ({ onShowLogin }) => {
  const [status, setStatus] = useState("verifying"); // verifying, success, error
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyEmail = async () => {
      // Get token from URL
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get("token");

      if (!token) {
        setStatus("error");
        setMessage("Invalid verification link");
        return;
      }

      try {
        const response = await authAPI.verifyEmail(token);
        setStatus("success");
        setMessage(response.data.message || "Email verified successfully!");
      } catch (err) {
        setStatus("error");
        setMessage(
          err.response?.data?.error ||
            "Failed to verify email. The link may have expired.",
        );
      }
    };

    verifyEmail();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md text-center">
        {status === "verifying" && (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4 animate-pulse">
              <Loader className="w-10 h-10 text-blue-600 animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Verifying Your Email...
            </h1>
            <p className="text-gray-600">Please wait a moment</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Email Verified!
            </h1>
            <p className="text-gray-600 mb-6">{message}</p>
            <button
              onClick={onShowLogin}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Continue to Login
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
              <XCircle className="w-10 h-10 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Verification Failed
            </h1>
            <p className="text-gray-600 mb-6">{message}</p>
            <button
              onClick={onShowLogin}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Back to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
