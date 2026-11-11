import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import Login from "./pages/Login";
import ChatBox from "./pages/ChatBox";
import Dashboard from "./pages/Dashboard";

// Pages behind the sign in page
function RequireSignIn({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth();
  if (loading) return null;
  return session ? children : <Navigate to="/" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/chat" element={<RequireSignIn><ChatBox /></RequireSignIn>} />
        <Route path="/dashboard" element={<RequireSignIn><Dashboard /></RequireSignIn>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
