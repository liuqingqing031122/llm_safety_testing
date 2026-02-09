import React, { useState } from "react";
import "./App.css";

function ResetPassword({ token, onComplete }) {
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (newPassword !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to reset password");
      }

      setMessage("Password reset successful! Redirecting...");

      // Redirect after 2 seconds
      setTimeout(() => {
        onComplete();
      }, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <div
        style={{
          background: "white",
          padding: "2.5rem",
          borderRadius: "16px",
          maxWidth: "450px",
          width: "90%",
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.3)",
        }}
      >
        <h2
          style={{ margin: "0 0 1.5rem 0", textAlign: "center", color: "#333" }}
        >
          Reset Your Password
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              placeholder="••••••••"
              autoComplete="new-password"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                border: "2px solid #e0e0e0",
                borderRadius: "8px",
                fontSize: "1rem",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div className="form-group" style={{ marginTop: "1rem" }}>
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="••••••••"
              autoComplete="new-password"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                border: "2px solid #e0e0e0",
                borderRadius: "8px",
                fontSize: "1rem",
                boxSizing: "border-box",
              }}
            />
          </div>

          {error && (
            <div
              style={{
                background: "#fee",
                color: "#c33",
                padding: "0.75rem",
                borderRadius: "6px",
                marginTop: "1rem",
                fontSize: "0.9rem",
                border: "1px solid #fcc",
              }}
            >
              {error}
            </div>
          )}

          {message && (
            <div
              style={{
                background: "#d4edda",
                color: "#155724",
                padding: "0.75rem",
                borderRadius: "6px",
                marginTop: "1rem",
                fontSize: "0.9rem",
                border: "1px solid #c3e6cb",
              }}
            >
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !!message}
            style={{
              width: "100%",
              padding: "0.875rem",
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "1rem",
              fontWeight: "600",
              cursor: loading || message ? "not-allowed" : "pointer",
              marginTop: "1.5rem",
              opacity: loading || message ? 0.6 : 1,
            }}
          >
            {loading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ResetPassword;
