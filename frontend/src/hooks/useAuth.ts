import { useCallback, useState } from 'react';

import { api } from '../services/api';
import { cloudLogin } from '../services/cloudApi';

import type { UserInfo } from '../services/api';

const TOKEN_KEY = 'llm_kb_token';
const USER_KEY = 'llm_kb_user';
const AUTH_MODE_KEY = 'auth_mode';

export type AuthMode = 'local' | 'cloud';

interface AuthState {
  user: UserInfo | null;
  loading: boolean;
  authMode: AuthMode;
}

function loadInitialState(): AuthState {
  const storedMode = (localStorage.getItem(AUTH_MODE_KEY) as AuthMode) || 'local';
  const storedToken = localStorage.getItem(TOKEN_KEY);
  const storedUser = localStorage.getItem(USER_KEY);

  if (storedToken && storedUser) {
    api.setToken(storedToken);
    try {
      const parsedUser: UserInfo = JSON.parse(storedUser);
      return { user: parsedUser, loading: false, authMode: storedMode };
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      api.setToken(null);
    }
  }

  return { user: null, loading: false, authMode: storedMode };
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(loadInitialState);

  const setAuthMode = useCallback((mode: AuthMode) => {
    localStorage.setItem(AUTH_MODE_KEY, mode);
    setState((prev) => ({ ...prev, authMode: mode }));
  }, []);

  const login = useCallback(
    async (credentials: { username: string; password: string } | { email: string; password: string }) => {
      if (state.authMode === 'cloud') {
        const { email, password } = credentials as { email: string; password: string };
        const result = await cloudLogin(email, password);

        localStorage.setItem('access_token', result.access_token);
        if (result.license_token) {
          localStorage.setItem('license_token', result.license_token);
        }
        localStorage.setItem('user_tier', result.tier || 'trial');
        localStorage.setItem('user_email', result.user?.email || '');

        api.setToken(result.access_token);

        const user: UserInfo = { id: result.user?.id || '', username: result.user?.email || email };
        localStorage.setItem(TOKEN_KEY, result.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        setState({ user, loading: false, authMode: 'cloud' });
      } else {
        const { username, password } = credentials as { username: string; password: string };
        const tokenResponse = await api.login(username, password);

        const user: UserInfo = { id: '', username };
        localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        setState({ user, loading: false, authMode: 'local' });
      }
    },
    [state.authMode],
  );

  const setup = useCallback(async (username: string, password: string) => {
    const tokenResponse = await api.setup(username, password);
    const user: UserInfo = { id: '', username };

    api.setToken(tokenResponse.access_token);
    localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({ user, loading: false, authMode: 'local' });
  }, []);

  const logout = useCallback(() => {
    api.setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem('access_token');
    localStorage.removeItem('license_token');
    localStorage.removeItem('user_tier');
    localStorage.removeItem('user_email');

    setState((prev) => ({ user: null, loading: false, authMode: prev.authMode }));
  }, []);

  return {
    user: state.user,
    loading: state.loading,
    authMode: state.authMode,
    setAuthMode,
    login,
    logout,
    setup,
  };
}
