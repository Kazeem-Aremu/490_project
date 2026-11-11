import { type FormEvent, useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import "../App.css";
import { supabase } from '../supabaseClient'
import { useAuth } from "../contexts/AuthContext";

type View = "login" | "signup" | "forgot" | "reset";

const headings: Record<View, { title: string; description: string; button: string }> = {
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
  // Shown when the student opens the link from the reset email
  reset: {
    title: "Choose a new password",
    description: "Enter a new password for your account.",
    button: "Save Password",
  },
};

function Login() {
  const [view, setView] = useState<View>("login");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const { session, lastEvent } = useAuth();

  const isSignup = view === "signup";
  const isForgot = view === "forgot";
  const isReset = view === "reset";

  // The reset email signs the student in with a recovery session; ask for the new password
  useEffect(() => {
    if (lastEvent === "PASSWORD_RECOVERY") setView("reset");
  }, [lastEvent]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) {
      setMessage("Sign in isn't set up yet: add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to .env.local.");
      return;
    }
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    setMessage("");
    setBusy(true);
    try {
      if (isForgot) {
        const { error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: window.location.origin + "/" });
        if (error) throw error;
        setMessage("If an account exists for that email, a reset link is on its way.");
      } else if (isSignup || isReset) {
        if (password !== String(form.get("confirmPassword") ?? "")) {
          setMessage("The passwords don't match.");
          return;
        }
        if (isReset) {
          const { error } = await supabase.auth.updateUser({ password });
          if (error) throw error;
          navigate("/dashboard");
          return;
        }
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              first_name: String(form.get("firstName") ?? "").trim(),
              last_name: String(form.get("lastName") ?? "").trim(),
              role: form.get("role") === "teacher" ? "teacher" : "student", // read by the server on first sign in
            },
            emailRedirectTo: window.location.origin + "/",
          },
        });
        if (error) throw error;
        if (data.session) navigate("/dashboard");
        else setMessage("Account created! Check your email to confirm it, then sign in.");
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        navigate("/dashboard");
      }
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function changeView(nextView: View) {
    setView(nextView);
    setMessage("");
  }

  // Already signed in (and not resetting a password): go straight in
  if (session && !isReset && lastEvent !== "PASSWORD_RECOVERY") return <Navigate to="/dashboard" replace />;

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
                  <fieldset className="role-choice">
                    <legend>I am a</legend>
                    <label>
                      <input type="radio" name="role" value="student" defaultChecked />
                      <span>Student</span>
                    </label>
                    <label>
                      <input type="radio" name="role" value="teacher" />
                      <span>Teacher</span>
                    </label>
                  </fieldset>

                  <div className="input-group">
                    <label htmlFor="firstName">First name</label>
                    <input
                      id="firstName"
                      name="firstName"
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
                      name="lastName"
                      type="text"
                      placeholder="Enter your last name"
                      autoComplete="family-name"
                      required
                    />
                  </div>
                </>
              )}

              {!isReset && (
                <div className="input-group">
                  <label htmlFor="email">Email address</label>
                  <input id="email" name="email" type="email" placeholder="you@example.com" autoComplete="email" required />
                </div>
              )}

              {!isForgot && (
                <div className="input-group">
                  <label htmlFor="password">Password</label>
                  <input id="password" name="password" type="password" placeholder="Enter your password"
                    autoComplete={view === "login" ? "current-password" : "new-password"} minLength={6} required />
                </div>
              )}

              {(isSignup || isReset) && (
                <div className="input-group">
                  <label htmlFor="confirmPassword">Confirm password</label>
                  <input id="confirmPassword" name="confirmPassword" type="password" placeholder="Re-enter your password" autoComplete="new-password" required />
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

              <button className="submit-button" type="submit" disabled={busy}>
                {busy ? "Please wait…" : headings[view].button}
              </button>
            </form>

            {message && <p className="prototype-message">{message}</p>}

            {isReset ? null : isForgot ? (
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

export default Login;
