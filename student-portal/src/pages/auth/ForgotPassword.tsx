import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../../supabaseClient";
import { NOT_CONFIGURED, authError } from "./authMessages";

function ForgotPassword() {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!supabase) { setMessage(NOT_CONFIGURED); return; }
    setBusy(true);

    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    setBusy(false);
    if (error) {
      setMessage(authError(error));
    } else {
      setMessage("If an account exists for that email, a reset link will be sent.");
    }
  }

  return (
    <>
      <h2>Forgot your password?</h2>
      <p className="form-description">
        Enter the email linked to your account and we'll send you a link to reset your password.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" placeholder="you@example.com" autoComplete="email"
            value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>

        <button className="submit-button" type="submit" disabled={busy}>{busy ? "Please wait…" : "Send Reset Link"}</button>
      </form>

      {message && <p className="prototype-message">{message}</p>}

      <p className="switch-text">
        Remembered your password?
        <Link className="switch-button" to="/login">Back to sign in</Link>
      </p>
    </>
  );
}

export default ForgotPassword;
