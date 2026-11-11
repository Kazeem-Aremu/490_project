import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../../supabaseClient";
import { NOT_CONFIGURED, authError } from "./authMessages";

type Role = "student" | "teacher";

function Signup() {
  const [message, setMessage] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!supabase) { setMessage(NOT_CONFIGURED); return; }

    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    setBusy(true);
    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password: password,
      options: {
        data: {
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          role: role, // read by the server (AuthService) on the first sign in
        },
        emailRedirectTo: `${window.location.origin}/login`,
      },
    });
    setBusy(false);

    if (error) {
      setMessage(authError(error));
    } else if (data.session) {
      navigate("/dashboard"); // "Confirm email" is off in Supabase: signed in already
    } else {
      setMessage("Account created! Check your email to confirm it, then sign in.");
    }
  }

  return (
    <>
      <h2>Create your account</h2>
      <p className="form-description">Enter your details to get started.</p>

      <form onSubmit={handleSubmit}>
        <fieldset className="role-choice">
          <legend>I am a</legend>
          <label>
            <input type="radio" name="role" value="student" checked={role === "student"} onChange={() => setRole("student")} />
            <span>Student</span>
          </label>
          <label>
            <input type="radio" name="role" value="teacher" checked={role === "teacher"} onChange={() => setRole("teacher")} />
            <span>Teacher</span>
          </label>
        </fieldset>

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
          <input id="email" type="email" placeholder="you@example.com" autoComplete="email"
            value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" placeholder="Enter your password" autoComplete="new-password" minLength={6}
            value={password} onChange={(event) => setPassword(event.target.value)} required />
        </div>

        <div className="input-group">
          <label htmlFor="confirmPassword">Confirm password</label>
          <input id="confirmPassword" type="password" placeholder="Re-enter your password" autoComplete="new-password"
            value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
        </div>

        <button className="submit-button" type="submit" disabled={busy}>{busy ? "Please wait…" : "Create Account"}</button>
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
