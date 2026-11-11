import { Outlet } from "react-router-dom";
import "./Auth.css";

function AuthLayout() {
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
