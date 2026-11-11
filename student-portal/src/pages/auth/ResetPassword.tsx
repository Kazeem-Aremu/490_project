import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../../supabaseClient";
import { useAuth } from "../../contexts/AuthContext";
import { NOT_CONFIGURED, authError } from "./authMessages";

// Opened from the reset email: Supabase signs the user in with a recovery session first.
function ResetPassword() {
  const { session } = useAuth();
  const [message, setMessage] = useState("");
  const [done, setDone] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!supabase) { setMessage(NOT_CONFIGURED); return; }
    if (!session) {
      setMessage("This page only works from the link in a password reset email. Use \"Forgot password?\" on the sign in page to get a new one.");
      return;
    }

    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    setBusy(true);
    const { error } = await supabase.auth.updateUser({ password: password });
    setBusy(false);

    if (error) {
      setMessage(authError(error));
    } else {
      setDone(true);
      setMessage("Your password has been updated.");
    }
  }

  return (
    <>
      <h2>Set a new password</h2>
      <p className="form-description">Choose a new password for your account.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="password">New password</label>
          <input id="password" type="password" placeholder="Enter a new password" autoComplete="new-password" minLength={6}
            value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="confirmPassword">Confirm new password</label>
          <input id="confirmPassword" type="password" placeholder="Re-enter your new password" autoComplete="new-password"
            value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
        </div>

        <button className="submit-button" type="submit" disabled={busy || done}>{busy ? "Please wait…" : "Update Password"}</button>
      </form>

      {message && <p className="prototype-message">{message}</p>}

      <p className="switch-text">
        {done ? <>Continue to
          <Link className="switch-button" to="/dashboard">your dashboard</Link></>
          : <>Back to
          <Link className="switch-button" to="/login">Sign in</Link></>}
      </p>
    </>
  );
}

export default ResetPassword;
