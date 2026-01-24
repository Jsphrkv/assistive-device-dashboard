import React from "react";
import { isAuthenticated } from "../services/authService";

const ProtectedRoute = ({ children, redirectTo = "/login" }) => {
  if (!isAuthenticated()) {
    window.location.href = redirectTo;
    return null;
  }

  return children;
};

export default ProtectedRoute;
