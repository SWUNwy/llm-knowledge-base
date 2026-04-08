import { useCallback, useEffect, useState } from 'react';

import { api } from '../services/api';

import type { UserInfo } from '../services/api';

const TOKEN_KEY = 'llm_kb_token';
const USER_KEY = 'llm_kb_user';

interface AuthState {
  user: UserInfo | null;
  loading: boolean;
  isSetupRequired: boolean;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    isSetupRequired: false,
  });

  // On mount, restore session from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);

    if (storedToken && storedUser) {
      api.setToken(storedToken);

      try {
        const parsedUser: UserInfo = JSON.parse(storedUser);
        setState({ user: parsedUser, loading: false, isSetupRequired: false });
      } catch {
        // Corrupted stored data — clear it
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        api.setToken(null);
        setState({ user: null, loading: false, isSetupRequired: false });
      }
    } else {
      setState((prev) => ({ ...prev, loading: false }));
    }
  }, []);

  const setup = useCallback(async (username: string, password: string) => {
    const tokenResponse = await api.setup(username, password);
    const user: UserInfo = {
      id: '',
      username,
    };

    api.setToken(tokenResponse.access_token);
    localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({ user, loading: false, isSetupRequired: false });
    return tokenResponse;
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const tokenResponse = await api.login(username, password);
    const user: UserInfo = {
      id: '',
      username,
    };

    api.setToken(tokenResponse.access_token);
    localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({ user, loading: false, isSetupRequired: false });
    return tokenResponse;
  }, []);

  const logout = useCallback(() => {
    api.setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    setState({ user: null, loading: false, isSetupRequired: false });
  }, []);

  return {
    user: state.user,
    loading: state.loading,
    login,
    logout,
    setup,
    isSetupRequired: state.isSetupRequired,
  };
}
