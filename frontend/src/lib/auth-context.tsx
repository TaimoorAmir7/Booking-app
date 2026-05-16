"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Tokens, User } from "@/types";

const STORAGE_KEY = "appointment_assistant_auth";

type StoredAuth = {
  user: User;
  tokens: Tokens;
};

type AuthContextValue = {
  user: User | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  getAccessToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function loadStored(): StoredAuth | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredAuth) : null;
  } catch {
    return null;
  }
}

function saveStored(data: StoredAuth | null) {
  if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  else localStorage.removeItem(STORAGE_KEY);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<Tokens | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = loadStored();
    if (stored) {
      setUser(stored.user);
      setTokens(stored.tokens);
      api.me(stored.tokens.access).catch(() => {
        saveStored(null);
        setUser(null);
        setTokens(null);
      });
    }
    setLoading(false);
  }, []);

  const persist = useCallback((data: StoredAuth) => {
    setUser(data.user);
    setTokens(data.tokens);
    saveStored(data);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const data = await api.login({ email, password });
      persist({ user: data.user, tokens: data.tokens });
      router.push("/dashboard");
    },
    [persist, router]
  );

  const signup = useCallback(
    async (email: string, password: string, fullName: string) => {
      const data = await api.signup({
        email,
        password,
        full_name: fullName,
      });
      persist({ user: data.user, tokens: data.tokens });
      router.push("/dashboard");
    },
    [persist, router]
  );

  const logout = useCallback(() => {
    saveStored(null);
    setUser(null);
    setTokens(null);
    router.push("/login");
  }, [router]);

  const getAccessToken = useCallback(async () => {
    if (!tokens) return null;
    try {
      await api.me(tokens.access);
      return tokens.access;
    } catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 404)) {
        if (e.status === 404) {
          logout();
          return null;
        }
      } else if (!(e instanceof ApiError) || e.status !== 401) {
        throw e;
      }
    }
    try {
      const refreshed = await api.refresh(tokens.refresh);
      const next = { ...tokens, access: refreshed.access };
      setTokens(next);
      if (user) saveStored({ user, tokens: next });
      return next.access;
    } catch {
      logout();
      return null;
    }
  }, [tokens, user, logout]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken: tokens?.access ?? null,
      loading,
      login,
      signup,
      logout,
      getAccessToken,
    }),
    [user, tokens, loading, login, signup, logout, getAccessToken]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
