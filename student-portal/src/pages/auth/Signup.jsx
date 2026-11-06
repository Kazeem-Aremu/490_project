import { useState } from "react";
import { Link } from "react-router-dom";

function Signup() {
  const [message, setMessage] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    setMessage("Prototype only! Authentication will be added later.");
  }

  return (
    <>
      <h2>Create your account</h2>
      <p className="form-description">Enter your details to get started.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="firstName">First name</label>
          <input id="firstName" type="text" placeholder="Enter your first name" autoComplete="given-name" required />
        </div>

        <div className="input-group">
          <label htmlFor="lastName">Last name</label>
          <input id="lastName" type="text" placeholder="Enter your last name" autoComplete="family-name" required />
        </div>

        <div className="input-group">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" placeholder="you@example.com" required />
        </div>

        <div className="input-group">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" placeholder="Enter your password" required />
        </div>

        <div className="input-group">
          <label htmlFor="confirmPassword">Confirm password</label>
          <input id="confirmPassword" type="password" placeholder="Re-enter your password" required />
        </div>

        <button className="submit-button" type="submit">Create Account</button>
      </form>

      {message && <p className="prototype-message">{message}</p>}

      <p className="switch-text">
        Already have an account?
        <Link className="switch-button" to="/login">Sign in</Link>
      </p>
    </>
  );
}

export default Signup;
