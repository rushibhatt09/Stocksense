import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import { useAuth } from "./auth/AuthContext";
import Adjustments from "./pages/Adjustments";
import Dashboard from "./pages/Dashboard";
import Deliveries from "./pages/Deliveries";
import ForgotPassword from "./pages/ForgotPassword";
import Login from "./pages/Login";
import MoveHistory from "./pages/MoveHistory";
import NotFound from "./pages/NotFound";
import Products from "./pages/Products";
import Profile from "./pages/Profile";
import Receipts from "./pages/Receipts";
import SettingsWarehouses from "./pages/SettingsWarehouses";
import Signup from "./pages/Signup";
import Transfers from "./pages/Transfers";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/products" element={<Products />} />
        <Route path="/receipts" element={<Receipts />} />
        <Route path="/deliveries" element={<Deliveries />} />
        <Route path="/transfers" element={<Transfers />} />
        <Route path="/adjustments" element={<Adjustments />} />
        <Route path="/moves" element={<MoveHistory />} />
        <Route path="/settings/warehouses" element={<SettingsWarehouses />} />
        <Route path="/profile" element={<Profile />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
