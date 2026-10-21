
import { useState } from "react";
import "./App.css";

function App() {
  const [isSignup, setIsSignup] = useState(false);
  const [message, setMessage] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    setMessage("Prototype only! Authentication will be added later.");
  }

  function switchForm() {
    setIsSignup(!isSignup);
    setMessage("");
  }

  return (
    <main className="page">
      <section className="auth-card">
        <div className="welcome-panel">
          <div className="logo">S</div>
          <p className="eyebrow">YOUR LEARNING SPACE</p>
          <h1>Learn, grow, and reach your goals.</h1>
          <p className="welcome-text">
            Your space to learn, track your progress,
            and work toward your academic goals.
          </p>
          <div className="welcome-footer">Insert Catchy Line Here</div>
        </div>

        <div className="form-panel">
          <div className="mobile-logo">S</div>
          <p className="eyebrow form-eyebrow">HAWK STUDENT PORTAL</p>
          <h2>{isSignup ? "Create your account" : "Welcome back!"}</h2>
          <p className="form-description">
            {isSignup
              ? "Enter your details to get started."
              : "Sign in to continue to your account."}
          </p>

          <form onSubmit={handleSubmit}>
            {isSignup && (
              <div className="input-group">
                <label htmlFor="fullName">Full name</label>
                <input id="fullName" type="text" placeholder="Enter your name" required />
              </div>
            )}

            <div className="input-group">
              <label htmlFor="email">Email address</label>
              <input id="email" type="email" placeholder="you@example.com" required />
            </div>

            <div className="input-group">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" placeholder="Enter your password" required />
            </div>

            {isSignup && (
              <div className="input-group">
                <label htmlFor="confirmPassword">Confirm password</label>
                <input id="confirmPassword" type="password" placeholder="Re-enter your password" required />
              </div>
            )}

            {!isSignup && (
              <div className="form-options">
                <label className="remember-option">
                  <input type="checkbox" />
                  Remember me
                </label>
                <span className="muted-link">Forgot password?</span>
              </div>
            )}

            <button className="submit-button" type="submit">
              {isSignup ? "Create Account" : "Sign In"}
            </button>
          </form>

          {message && <p className="prototype-message">{message}</p>}

          <p className="switch-text">
            {isSignup ? "Already have an account?" : "Don't have an account?"}
            <button className="switch-button" type="button" onClick={switchForm}>
              {isSignup ? "Sign in" : "Sign up"}
            </button>
          </p>

          <p className="legal-text">Student Portal Prototype</p>
        </div>
      </section>
    </main>
  );
}

export default App;
