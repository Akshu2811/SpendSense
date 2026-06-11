import React, { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin, logout as apiLogout, getCurrentBudget } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password);
    setUser({ username: data.username ?? username });

    let complete = false;
    try {
      const budget = await getCurrentBudget();
      complete = Boolean(budget?.master_monthly > 0);
    } catch {
      complete = false;
    }
    setOnboardingComplete(complete);

    // Return complete flag so callers can navigate immediately without
    // waiting for a re-render to pick up the updated state value.
    return { ...data, onboardingComplete: complete };
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setUser(null);
    setOnboardingComplete(false);
  }, []);

  const completeOnboarding = useCallback(() => {
    setOnboardingComplete(true);
  }, []);

  return (
    <AuthContext.Provider value={{ user, onboardingComplete, login, logout, completeOnboarding }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};
