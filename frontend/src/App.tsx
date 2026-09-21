import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { RedirectAfterLogin } from "./pages/RedirectAfterLogin";
import { ClientDashboardPage } from "./pages/ClientDashboardPage";
import { VehicleHistoryPage } from "./pages/VehicleHistoryPage";
import { GarageDashboardPage } from "./pages/GarageDashboardPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/redirect" element={<RedirectAfterLogin />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute roles={["CLIENT"]}>
              <ClientDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vehicles/:id/history"
          element={
            <ProtectedRoute roles={["CLIENT"]}>
              <VehicleHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/garage"
          element={
            <ProtectedRoute roles={["GARAGE_ADMIN", "GARAGE_STAFF"]}>
              <GarageDashboardPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
