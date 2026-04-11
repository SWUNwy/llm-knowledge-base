// website/lib/auth-client.ts
// Client-side auth utilities for JWT token management

const TOKEN_KEY = 'kb_access_token';
const USER_KEY = 'kb_user';

export interface AuthUser {
  id: string;
  email: string;
  tier?: string;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setUser(user: AuthUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

export function decodeJWTPayload(token: string): Record<string, unknown> | null {
  try {
    const base64 = token.split('.')[1];
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeJWTPayload(token);
  if (!payload?.exp) return true;
  return (payload.exp as number) * 1000 < Date.now();
}

export function getValidToken(): string | null {
  const token = getToken();
  if (!token || isTokenExpired(token)) {
    clearAuth();
    return null;
  }
  return token;
}
