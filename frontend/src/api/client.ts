import type { UserProfile } from "../domain/types";

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  offline_grace_until: string;
  user: UserProfile;
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

let inMemoryAccessToken: string | null = null;
let onUnauthorizedCallback: (() => void) | null = null;
let refreshPromise: Promise<AuthTokenResponse | null> | null = null;

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
}

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setOnUnauthorized(cb: (() => void) | null): void {
  onUnauthorizedCallback = cb;
}

async function parseError(resp: Response): Promise<ApiError> {
  try {
    const body = (await resp.json()) as {
      error?: { code?: string; message?: string };
      detail?: string;
    };
    const code = body.error?.code ?? `HTTP_${resp.status}`;
    const msg = body.error?.message ?? body.detail ?? `Error HTTP ${resp.status}`;
    return new ApiError(resp.status, code, msg);
  } catch {
    return new ApiError(resp.status, `HTTP_${resp.status}`, `Error HTTP ${resp.status}`);
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  retryOn401 = true
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (inMemoryAccessToken) {
    headers.set("Authorization", `Bearer ${inMemoryAccessToken}`);
  }

  const resp = await fetch(path, {
    ...init,
    headers,
    credentials: "include",
  });

  if (resp.status === 401 && retryOn401 && !path.includes("/auth/login") && !path.includes("/auth/refresh")) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiFetch<T>(path, init, false);
    }
    if (onUnauthorizedCallback) {
      onUnauthorizedCallback();
    }
  }

  if (!resp.ok) {
    throw await parseError(resp);
  }
  return (await resp.json()) as T;
}

export async function tryRefreshToken(): Promise<AuthTokenResponse | null> {
  if (refreshPromise) {
    return refreshPromise;
  }
  refreshPromise = (async () => {
    try {
      const resp = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
      });
      if (!resp.ok) return null;
      const data = (await resp.json()) as AuthTokenResponse;
      setAccessToken(data.access_token);
      return data;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}
