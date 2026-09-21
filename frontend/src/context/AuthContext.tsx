import { createContext, useContext, useMemo, useState, ReactNode } from "react";
import { apiRequest, setToken, getToken } from "../api/client";
import { AuthUser } from "../api/types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  loginClient: (email: string, password: string) => Promise<void>;
  loginGarage: (email: string, password: string) => Promise<void>;
  registerClient: (input: { name: string; email: string; phone?: string; password: string }) => Promise<void>;
  registerGarage: (input: {
    garageName: string;
    city: string;
    address: string;
    garagePhone: string;
    garageEmail?: string;
    adminName: string;
    adminEmail: string;
    adminPassword: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthResponse {
  token: string;
  user: AuthUser;
}

function readStoredUser(): AuthUser | null {
  const raw = localStorage.getItem("garage_app_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => (getToken() ? readStoredUser() : null));
  const [loading, setLoading] = useState(false);

  function persist(auth: AuthResponse) {
    setToken(auth.token);
    localStorage.setItem("garage_app_user", JSON.stringify(auth.user));
    setUser(auth.user);
  }

  async function loginClient(email: string, password: string) {
    setLoading(true);
    try {
      const auth = await apiRequest<AuthResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      persist(auth);
    } finally {
      setLoading(false);
    }
  }

  const loginGarage = loginClient;

  async function registerClient(input: { name: string; email: string; phone?: string; password: string }) {
    setLoading(true);
    try {
      const auth = await apiRequest<AuthResponse>("/auth/register/client", {
        method: "POST",
        body: input,
      });
      persist(auth);
    } finally {
      setLoading(false);
    }
  }

  async function registerGarage(input: {
    garageName: string;
    city: string;
    address: string;
    garagePhone: string;
    garageEmail?: string;
    adminName: string;
    adminEmail: string;
    adminPassword: string;
  }) {
    setLoading(true);
    try {
      const auth = await apiRequest<AuthResponse>("/auth/register/garage", {
        method: "POST",
        body: input,
      });
      persist(auth);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    setToken(null);
    localStorage.removeItem("garage_app_user");
    setUser(null);
  }

  const value = useMemo(
    () => ({ user, loading, loginClient, loginGarage, registerClient, registerGarage, logout }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth doit être utilisé dans un AuthProvider");
  }
  return ctx;
}
