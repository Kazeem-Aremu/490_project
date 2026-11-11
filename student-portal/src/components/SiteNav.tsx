import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useWebSocket } from "../contexts/ClientContextProvider";
import "./SiteNav.css";

// Thin bar shared by the signed-in pages so they link to each other
export default function SiteNav() {
  const { session, serverUser, signOut } = useAuth();
  const { isConnected } = useWebSocket();
  const navigate = useNavigate();

  async function onSignOut() {
    await signOut();
    navigate("/login");
  }

  return (
    <nav className="site-nav" aria-label="Portal">
      <span className="site-nav-logo">H</span>
      <NavLink to="/dashboard">Dashboard</NavLink>
      {serverUser?.ROLE?.toLowerCase() !== "teacher" && <NavLink to="/chat">AI Chat</NavLink>}
      <span className="site-nav-spacer" />
      <span className={"site-nav-dot" + (isConnected ? " on" : "")} title={isConnected ? "Server connected" : "Server not connected"} />
      <span className="site-nav-who">{serverUser?.NAME || session?.user.email}</span>
      <button type="button" onClick={onSignOut}>Log out</button>
    </nav>
  );
}
