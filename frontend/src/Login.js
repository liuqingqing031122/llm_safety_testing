import React, { useState } from "react";
import { useAuth } from "./AuthContext";
import "./Auth.css";

function Login({ onSwitchToRegister, onClose, onForgotPassword }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Login failed");
      }

      const data = await response.json();
      login(data.access_token, data.user);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ✅ NEW: Google OAuth login
  const handleGoogleLogin = () => {
    // Redirect to backend Google OAuth endpoint
    window.location.href = "http://localhost:8000/api/auth/google/login";
  };

  const handleGithubLogin = () => {
    window.location.href = "http://localhost:8000/api/auth/github/login";
  };

  return (
    <div className="auth-form">
      <h2>Welcome Back</h2>
      {/* ✅ NEW: OAuth buttons section */}
      <div className="oauth-buttons">
        <button
          type="button"
          onClick={handleGoogleLogin}
          className="oauth-btn google-btn"
        >
          <span className="oauth-icon">🔵</span>
          Continue with Google
        </button>
        <button
          type="button"
          onClick={handleGithubLogin}
          className="oauth-btn github-btn"
        >
          <span className="oauth-icon">⚫</span>
          Continue with GitHub
        </button>
      </div>

      <div className="auth-divider">
        <span>or</span>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="your@email.com"
            autoComplete="email"
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </div>

        <div
          className="form-group"
          style={{ textAlign: "right", marginTop: "-0.5rem" }}
        >
          <button
            type="button"
            onClick={onForgotPassword}
            className="link-button"
            style={{ fontSize: "0.85rem" }}
          >
            Forgot password?
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      <p className="auth-switch">
        Don't have an account?{" "}
        <button onClick={onSwitchToRegister} className="link-button">
          Register
        </button>
      </p>
    </div>
  );
}

export default Login;
