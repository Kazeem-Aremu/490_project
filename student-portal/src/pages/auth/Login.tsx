import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../../supabaseClient";
import { NOT_CONFIGURED, authError } from "./authMessages";

function Login() {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!supabase) { setMessage(NOT_CONFIGURED); return; }
    setBusy(true);

    const { error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password: password,
    });

    setBusy(false);
    if (error) {
      setMessage(authError(error));
    } else {
      navigate("/dashboard");
    }
  }

  return (
    <>
      <h2>Welcome back!</h2>
      <p className="form-description">Sign in to continue to your account.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" placeholder="you@example.com" autoComplete="email"
            value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" placeholder="Enter your password" autoComplete="current-password"
            value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>

        <div className="form-options">
          <label className="remember-option">
            <input type="checkbox" />
            Remember me
          </label>
          <Link className="muted-link" to="/forgot-password">Forgot password?</Link>
        </div>

        <button className="submit-button" type="submit" disabled={busy}>{busy ? "Please wait…" : "Sign In"}</button>
      </form>

      {message && <p className="prototype-message">{message}</p>}

      <p className="switch-text">
        Don't have an account?
        <Link className="switch-button" to="/signup">Sign up</Link>
      </p>
    </>
  );
}

export default Login;
