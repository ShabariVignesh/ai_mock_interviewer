import React, { useState, createContext, useContext } from 'react';
interface AuthContextType {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string) => Promise<void>;
}
const AuthContext = createContext<AuthContextType | null>(null);
export function AuthProvider({
  children
}: {
  children: React.ReactNode;
}) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const login = async (email: string, password: string) => {
    // TODO: Implement actual authentication
    setIsAuthenticated(true);
  };
  const logout = () => {
    setIsAuthenticated(false);
  };
  const register = async (email: string, password: string) => {
    // TODO: Implement actual registration
    setIsAuthenticated(true);
  };
  return <AuthContext.Provider value={{
    isAuthenticated,
    login,
    logout,
    register
  }}>
      {children}
    </AuthContext.Provider>;
}
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};