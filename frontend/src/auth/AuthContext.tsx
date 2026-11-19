import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  apiFetch,
  setAccessToken,
  setOnUnauthorized,
  tryRefreshToken,
  type AuthTokenResponse,
} from "../api/client";
import { db } from "../db/schema";
import { runSyncCycle } from "../db/syncEngine";
import type { UserProfile } from "../domain/types";

interface AuthContextValue {
  user: UserProfile | null;
  loading: boolean;
  isOfflineSession: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (perm: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }): React.ReactElement {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOfflineSession, setIsOfflineSession] = useState(false);

  const persistOfflineSession = useCallback(async (res: AuthTokenResponse): Promise<void> => {
    await db.offline_session.put({
      key: "current",
      user: res.user,
      offline_grace_until: res.offline_grace_until,
      saved_at: new Date().toISOString(),
    });
  }, []);

  const restoreOfflineSession = useCallback(async (): Promise<boolean> => {
    const cached = await db.offline_session.get("current");
    if (!cached) return false;
    if (new Date(cached.offline_grace_until).getTime() <= Date.now()) {
      await db.offline_session.delete("current");
      return false;
    }
    setUser(cached.user);
    setIsOfflineSession(true);
    return true;
  }, []);

  useEffect(() => {
    setOnUnauthorized(() => {
      if (navigator.onLine) {
        setAccessToken(null);
      }
    });

    const bootstrap = async (): Promise<void> => {
      setLoading(true);
      try {
        if (navigator.onLine) {
          const refreshed = await tryRefreshToken();
          if (refreshed) {
            setUser(refreshed.user);
            setIsOfflineSession(false);
            await persistOfflineSession(refreshed);
            void runSyncCycle();
            return;
          }
        }
        await restoreOfflineSession();
      } finally {
        setLoading(false);
      }
    };
    void bootstrap();

    const handleOnline = (): void => {
      void (async () => {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
          setUser(refreshed.user);
          setIsOfflineSession(false);
          await persistOfflineSession(refreshed);
        }
        await runSyncCycle(db, true);
      })();
    };
    window.addEventListener("online", handleOnline);
    return () => window.removeEventListener("online", handleOnline);
  }, [persistOfflineSession, restoreOfflineSession]);

  const login = useCallback(
    async (identifier: string, password: string): Promise<void> => {
      const res = await apiFetch<AuthTokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ identifier, password }),
      });
      setAccessToken(res.access_token);
      setUser(res.user);
      setIsOfflineSession(false);
      await persistOfflineSession(res);
      await runSyncCycle(db, true);
    },
    [persistOfflineSession]
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      if (navigator.onLine) {
        await apiFetch("/api/v1/auth/logout", { method: "POST" });
      }
    } catch {
      // Cierra sesión localmente incluso si el servidor no responde
    } finally {
      setAccessToken(null);
      setUser(null);
      setIsOfflineSession(false);
      await db.offline_session.delete("current");
    }
  }, []);

  const hasPermission = useCallback(
    (perm: string): boolean => {
      return Boolean(user?.permissions.includes(perm));
    },
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, isOfflineSession, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe utilizarse dentro de AuthProvider.");
  return ctx;
}
