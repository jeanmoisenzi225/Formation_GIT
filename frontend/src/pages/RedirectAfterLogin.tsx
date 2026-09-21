import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RedirectAfterLogin() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role === "CLIENT") {
    return <Navigate to="/dashboard" replace />;
  }

  return <Navigate to="/garage" replace />;
}
