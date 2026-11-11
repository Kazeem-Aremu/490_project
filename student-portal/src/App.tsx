import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import AuthLayout from "./pages/auth/AuthLayout";
import Login from "./pages/auth/Login";
import Signup from "./pages/auth/Signup";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";
import ChatBox from "./pages/ChatBox";
import Dashboard from "./pages/Dashboard";

// Pages behind the sign in page
function RequireSignIn({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth();
  if (loading) return null;
  return session ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Sign in pages (Portia's split routes, shared AuthLayout) */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
        </Route>

        <Route path="/dashboard" element={<RequireSignIn><Dashboard /></RequireSignIn>} />
        <Route path="/chat" element={<RequireSignIn><ChatBox /></RequireSignIn>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
