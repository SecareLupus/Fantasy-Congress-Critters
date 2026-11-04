import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { post, type Me } from "./api";

type Session = {
  me: Me | null;
  loaded: boolean;
  refresh: () => Promise<void>;
  setMe: (me: Me | null) => void;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<Session | null>(null);

/** Who is signed in, shared by every page. */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loaded, setLoaded] = useState(false);
  const refresh = useCallback(async () => {
    const r = await fetch("/api/me");
    setMe(r.ok ? await r.json() : null);
    setLoaded(true);
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);
  const signOut = async () => {
    await post("/api/signout");
    setMe(null);
  };
  return <SessionContext.Provider value={{ me, loaded, refresh, setMe, signOut }}>{children}</SessionContext.Provider>;
}

export function useSession(): Session {
  return useContext(SessionContext)!;
}
