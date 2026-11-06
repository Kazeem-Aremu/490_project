import { useState } from "react";
import { Link } from "react-router-dom";

function ForgotPassword() {
  const [message, setMessage] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    setMessage("Prototype only! If an account exists for that email, a reset link will be sent once email is set up.");
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
          <input id="email" type="email" placeholder="you@example.com" required />
        </div>

        <button className="submit-button" type="submit">Send Reset Link</button>
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
