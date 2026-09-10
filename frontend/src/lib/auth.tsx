"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  ApiError,
  getMe,
  login as apiLogin,
  logout as apiLogout,
  setUnauthorizedHandler,
  signup as apiSignup,
  UserRecord,
} from "./api";

interface AuthState {
  user: UserRecord | null;
  /** True only until the initial session check resolves. */
  checking: boolean;
  login: (email: string, password: string) => Promise<void>;
  /** Resolves true when the new account is signed in, false when it
   *  still has to verify its email address first. */
  signup: (
    name: string,
    email: string,
    password: string,
  ) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserRecord | null>(null);
  const [checking, setChecking] = useState(true);

  // The session cookie is httpOnly, so JavaScript cannot read it to find
  // out whether we are logged in. The only way to know is to ask the
  // server — hence a /auth/me call on mount rather than a localStorage
  // check. That is the point of httpOnly: an XSS bug can't read the
  // session either.
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const me = await getMe();
        if (!cancelled) setUser(me);
      } catch {
        // 401 here is the normal "not logged in yet" case, not an error
        // worth surfacing.
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setChecking(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // Any 401 from any endpoint means the session died mid-use (the token
  // expires after an hour). Drop straight back to the sign-in screen
  // instead of leaving a logged-out user staring at a UI where every
  // action fails.
  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null));
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setUser(await apiLogin(email, password));
  }, []);

  const signup = useCallback(
    async (name: string, email: string, password: string) => {
      const result = await apiSignup(name, email, password);
      // Only adopt the user when the backend actually issued a session.
      // With verification required it creates the account but sets no
      // cookie, so treating this as "logged in" would drop an
      // unauthenticated user into the app where every call 401s.
      if (result.authenticated) {
        setUser(result.user);
      }
      return result.authenticated;
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch (err) {
      // A failed logout call still means the user wants out. Clearing
      // local state is the honest response — the cookie may already be
      // gone, which is what produced the error.
      if (!(err instanceof ApiError)) throw err;
    } finally {
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, checking, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider.");
  }
  return context;
}
