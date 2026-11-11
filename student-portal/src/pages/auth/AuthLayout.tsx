import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import "./Auth.css";

// Shared frame for the sign in pages (Portia's layout). Signed-in users go straight to the
// dashboard, except while choosing a new password from a reset email.
function AuthLayout() {
  const { session, loading, lastEvent } = useAuth();
  const { pathname } = useLocation();

  if (loading) return null;
  // The reset email signs the user in with a recovery session: send them to choose a password
  if (lastEvent === "PASSWORD_RECOVERY" && pathname !== "/reset-password") return <Navigate to="/reset-password" replace />;
  if (session && pathname !== "/reset-password") return <Navigate to="/dashboard" replace />;

  return (
    <main className="page">
      <section className="auth-card">
        <div className="welcome-panel">
          <div className="logo">H</div>
          <p className="eyebrow">YOUR LEARNING SPACE</p>
          <h1>Learn, grow, and reach your goals.</h1>
          <p className="welcome-text">
            Your space to learn, track your progress,
            and work toward your academic goals.
          </p>
          <div className="welcome-footer">Insert Catchy Line Here</div>
        </div>

        <div className="form-panel">
          <div className="mobile-logo">H</div>
          <p className="eyebrow form-eyebrow">Insert Title Here</p>

          <Outlet />

          <p className="legal-text">Student Login/Signup Page Prototype</p>
        </div>
      </section>
    </main>
  );
}

export default AuthLayout;
