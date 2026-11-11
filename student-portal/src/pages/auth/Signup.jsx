import { useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../../supabaseClient";

function Signup() {
  const [message, setMessage] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");

    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    const { error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: {
          first_name: firstName,
          last_name: lastName,
        },
      },
    });

    if (error) {
      setMessage(error.message);
    } else {
      setMessage("Account created! Check your email if confirmation is required.");
    }
  }

  return (
    <>
      <h2>Create your account</h2>
      <p className="form-description">Enter your details to get started.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="firstName">First name</label>
          <input id="firstName" type="text" placeholder="Enter your first name" autoComplete="given-name"
            value={firstName} onChange={(event) => setFirstName(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="lastName">Last name</label>
          <input id="lastName" type="text" placeholder="Enter your last name" autoComplete="family-name"
            value={lastName} onChange={(event) => setLastName(event.target.value)} required />
        </div>

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

        <div className="input-group">
          <label htmlFor="confirmPassword">Confirm password</label>
          <input id="confirmPassword" type="password" placeholder="Re-enter your password"
            value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
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
