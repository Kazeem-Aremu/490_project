import { createContext, type ReactNode, useContext, useEffect, useState } from "react";
import type { AuthChangeEvent, Session } from "@supabase/supabase-js";
import { supabase } from "../supabaseClient";
import { useWebSocket } from "./ClientContextProvider";

// A row from the server's USER table, plus the Supabase account it is linked to
export type ServerUser = {
  id: number;
  NAME: string;
  ROLE: string;
  AUTH_ID: string;
  EMAIL: string | null;
};

type AuthContextType = {
  session: Session | null;
  loading: boolean; // true until we know whether someone is signed in
  lastEvent: AuthChangeEvent | null;
  serverUser: ServerUser | null; // set once the Python server has verified the session
  serverError: string | null;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside an AuthProvider");
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const { request, isConnected } = useWebSocket();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastEvent, setLastEvent] = useState<AuthChangeEvent | null>(null);
  const [serverUser, setServerUser] = useState<ServerUser | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  useEffect(() => {
    if (!supabase) { setLoading(false); return; }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data } = supabase.auth.onAuthStateChange((event, next) => {
      setLastEvent(event);
      setSession(next);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  // Each WebSocket connection signs in with the current access token (also after refreshes/reconnects)
  const token = session?.access_token;
  useEffect(() => {
    if (!token || !isConnected) { setServerUser(null); return; }
    let alive = true;
    setServerError(null);
    request<{ USER: ServerUser }>({ MESSAGE: { METHOD: "POST", INFO: "login", PARAMS: { TOKEN: token } } })
      .then((m) => { if (alive) setServerUser(m.USER); })
      .catch((e: Error) => { if (alive) { setServerUser(null); setServerError(e.message); } });
    return () => { alive = false; };
  }, [token, isConnected, request]);

  async function signOut() {
    await supabase?.auth.signOut();
    setServerUser(null);
  }

  return (
    <AuthContext.Provider value={{ session, loading, lastEvent, serverUser, serverError, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
