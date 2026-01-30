import React, { createContext, useState, useContext, useEffect } from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rememberMe, setRememberMe] = useState(false);

  // Load token on mount
  useEffect(() => {
    // Try sessionStorage first (clears on tab close)
    let savedToken = sessionStorage.getItem("auth_token");
    let savedUser = sessionStorage.getItem("auth_user");
    let storage = "session";

    // If not in session, check localStorage (persists)
    if (!savedToken) {
      savedToken = localStorage.getItem("auth_token");
      savedUser = localStorage.getItem("auth_user");
      storage = "local";
    }

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setRememberMe(storage === "local");
    }

    // Always set loading to false, even if no user
    setLoading(false);
  }, []);

  const login = (token, user, remember = false) => {
    setToken(token);
    setUser(user);
    setRememberMe(remember);

    if (remember) {
      // Save to localStorage (persists across sessions)
      localStorage.setItem("auth_token", token);
      localStorage.setItem("auth_user", JSON.stringify(user));
    } else {
      // Save to sessionStorage (clears on tab close)
      sessionStorage.setItem("auth_token", token);
      sessionStorage.setItem("auth_user", JSON.stringify(user));
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setRememberMe(false);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    sessionStorage.removeItem("auth_token");
    sessionStorage.removeItem("auth_user");
    sessionStorage.clear(); // Clear conversation data too
  };

  return (
    <AuthContext.Provider
      value={{ user, token, login, logout, loading, rememberMe }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
