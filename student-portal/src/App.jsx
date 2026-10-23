import { useState } from "react";
import "./App.css";

const headings = {
  login: {
    title: "Welcome back!",
    description: "Sign in to continue to your account.",
    button: "Sign In",
  },
  signup: {
    title: "Create your account",
    description: "Enter your details to get started.",
    button: "Create Account",
  },
  forgot: {
    title: "Forgot your password?",
    description: "Enter the email linked to your account and we'll send you a link to reset your password.",
    button: "Send Reset Link",
  },
};

function App() {
  const [view, setView] = useState("login");
  const [message, setMessage] = useState("");

  const isSignup = view === "signup";
  const isForgot = view === "forgot";

  function handleSubmit(event) {
    event.preventDefault();
    if (isForgot) {
      setMessage("Prototype only! If an account exists for that email, a reset link will be sent once email is set up.");
    } else {
      setMessage("Prototype only! Authentication will be added later.");
    }
  }

  function changeView(nextView) {
    setView(nextView);
    setMessage("");
  }

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
          <h2>{headings[view].title}</h2>
          <p className="form-description">{headings[view].description}</p>

          <form onSubmit={handleSubmit}>
            {isSignup && (
              <>
                <div className="input-group">
                  <label htmlFor="firstName">First name</label>
                  <input
                    id="firstName"
                    type="text"
                    placeholder="Enter your first name"
                    autoComplete="given-name"
                    required
                  />
                </div>

                <div className="input-group">
                  <label htmlFor="lastName">Last name</label>
                  <input
                    id="lastName"
                    type="text"
                    placeholder="Enter your last name"
                    autoComplete="family-name"
                    required
                  />
                </div>
              </>
            )}

            <div className="input-group">
              <label htmlFor="email">Email address</label>
              <input id="email" type="email" placeholder="you@example.com" required />
            </div>

            {!isForgot && (
              <div className="input-group">
                <label htmlFor="password">Password</label>
                <input id="password" type="password" placeholder="Enter your password" required />
              </div>
            )}

            {isSignup && (
              <div className="input-group">
                <label htmlFor="confirmPassword">Confirm password</label>
                <input id="confirmPassword" type="password" placeholder="Re-enter your password" required />
              </div>
            )}

            {view === "login" && (
              <div className="form-options">
                <label className="remember-option">
                  <input type="checkbox" />
                  Remember me
                </label>
                <button className="muted-link" type="button" onClick={() => changeView("forgot")}>
                  Forgot password?
                </button>
              </div>
            )}

            <button className="submit-button" type="submit">
              {headings[view].button}
            </button>
          </form>

          {message && <p className="prototype-message">{message}</p>}

          {isForgot ? (
            <p className="switch-text">
              Remembered your password?
              <button className="switch-button" type="button" onClick={() => changeView("login")}>
                Back to sign in
              </button>
            </p>
          ) : (
            <p className="switch-text">
              {isSignup ? "Already have an account?" : "Don't have an account?"}
              <button
                className="switch-button"
                type="button"
                onClick={() => changeView(isSignup ? "login" : "signup")}
              >
                {isSignup ? "Sign in" : "Sign up"}
              </button>
            </p>
          )}

          <p className="legal-text">Student Login/Signup Page Prototype</p>
        </div>
      </section>
    </main>
  );
}

export default App;
