import React, { useState } from "react";
import { Camera, Eye, EyeOff, Mail, AlertCircle } from "lucide-react";
import { login } from "../services/authService";
import { authAPI } from "../services/api";

const LoginForm = ({ onLogin, onShowRegister, onShowForgotPassword }) => {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    showPassword: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [resendingEmail, setResendingEmail] = useState(false);

  const handleSubmit = async () => {
    console.log("=== SUBMIT STARTED ===");

    if (!formData.username || !formData.password) {
      setError("Please enter both username and password");
      return;
    }

    setLoading(true);
    setError("");
    setNeedsVerification(false);

    try {
      const result = await login(formData.username, formData.password);

      if (result.error) {
        // Check if it's an email verification error
        if (result.error === "Email not verified") {
          setNeedsVerification(true);
          setUserEmail(result.email || "");
          setError("Please verify your email before logging in");
        } else {
          setError(result.error);
        }
        setLoading(false);
        return;
      }

      onLogin(result.user);
    } catch (err) {
      setError("An unexpected error occurred");
      setLoading(false);
    }
  };

  const handleResendVerification = async () => {
    if (!userEmail) {
      setError("Email address not found. Please try registering again.");
      return;
    }

    setResendingEmail(true);
    try {
      await authAPI.resendVerification(userEmail);
      setError("");
      alert("Verification email sent! Please check your inbox.");
    } catch (err) {
      setError("Failed to resend verification email");
    } finally {
      setResendingEmail(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Camera className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Assistive Device Dashboard
          </h1>
          <p className="text-gray-600 text-sm">
            Wearable Computer Vision System
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              onKeyPress={handleKeyPress}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter username"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={formData.showPassword ? "text" : "password"}
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                onKeyPress={handleKeyPress}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() =>
                  setFormData({
                    ...formData,
                    showPassword: !formData.showPassword,
                  })
                }
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
              >
                {formData.showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p>{error}</p>
                {needsVerification && userEmail && (
                  <button
                    onClick={handleResendVerification}
                    disabled={resendingEmail}
                    className="mt-2 text-blue-600 hover:text-blue-700 font-medium underline disabled:opacity-50"
                  >
                    {resendingEmail
                      ? "Sending..."
                      : "Resend verification email"}
                  </button>
                )}
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={onShowForgotPassword}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Forgot password?
            </button>
          </div>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <button
              type="button"
              onClick={onShowRegister}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Sign up here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
