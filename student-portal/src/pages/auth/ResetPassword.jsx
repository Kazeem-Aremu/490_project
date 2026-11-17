import { useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../../supabaseClient";

function ResetPassword() {
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");

    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    const { error } = await supabase.auth.updateUser({ password: password });

    if (error) {
      setMessage(error.message);
    } else {
      setMessage("Your password has been updated. You can now sign in with your new password.");
    }
  }

  return (
    <>
      <h2>Set a new password</h2>
      <p className="form-description">Choose a new password for your account.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="password">New password</label>
          <input id="password" type="password" placeholder="Enter a new password" autoComplete="new-password"
            value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="confirmPassword">Confirm new password</label>
          <input id="confirmPassword" type="password" placeholder="Re-enter your new password" autoComplete="new-password"
            value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
        </div>

        <button className="submit-button" type="submit">Update Password</button>
      </form>

      {message && <p className="prototype-message">{message}</p>}

      <p className="switch-text">
        Back to
        <Link className="switch-button" to="/login">Sign in</Link>
      </p>
    </>
  );
}

export default ResetPassword;
