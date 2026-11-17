import { useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../../supabaseClient";

function Login() {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(event) {
  event.preventDefault();
  setMessage("");

  const { error } = await supabase.auth.signInWithPassword({
    email: email,
    password: password,
  });

  if (error) {
    setMessage(error.message);
  } else {
   setMessage("Login successful!");
  }
}

  return (
    <>
      <h2>Welcome back!</h2>
      <p className="form-description">Sign in to continue to your account.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" placeholder="you@example.com"
            value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" placeholder="Enter your password"
            value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>

        <div className="form-options">
          <label className="remember-option">
            <input type="checkbox" />
            Remember me
          </label>
          <Link className="muted-link" to="/forgot-password">Forgot password?</Link>
        </div>

        <button className="submit-button" type="submit">Sign In</button>
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
