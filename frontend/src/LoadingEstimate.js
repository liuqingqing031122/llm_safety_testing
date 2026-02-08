import React, { useState, useEffect } from "react";
import "./LoadingEstimate.css";

function LoadingEstimate({ type, modelCount = 1 }) {
  const [elapsed, setElapsed] = useState(0);

  // Estimate times based on type
  const estimates = {
    generating: {
      total: modelCount * 15, // 15 seconds per model
      message: "Generating responses from AI models...",
      icon: "🤖",
    },
    scoring: {
      total: 15, // 15 seconds for scoring
      message: "Analyzing responses against medical databases...",
      icon: "📊",
    },
  };

  const config = estimates[type] || estimates.generating;
  const progress = Math.min((elapsed / config.total) * 100, 99); // Cap at 99% until actually done

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed((prev) => prev + 0.1);
    }, 100);

    return () => clearInterval(timer);
  }, []);

  const remainingTime = Math.max(0, config.total - elapsed);

  return (
    <div className="loading-estimate">
      <div className="loading-content">
        <div className="loading-icon">{config.icon}</div>
        <h3 className="loading-title">{config.message}</h3>

        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="progress-info">
            <span className="progress-percent">{Math.round(progress)}%</span>
            <span className="progress-time">
              ~{Math.ceil(remainingTime)}s remaining
            </span>
          </div>
        </div>

        <div className="loading-steps">
          {type === "generating" && (
            <>
              <div
                className={`step ${
                  elapsed > 2 ? "completed" : elapsed > 0 ? "active" : ""
                }`}
              >
                <span className="step-icon">{elapsed > 2 ? "✓" : "○"}</span>
                <span className="step-text">Connecting to AI models</span>
              </div>
              <div
                className={`step ${
                  elapsed > config.total * 0.3
                    ? "completed"
                    : elapsed > 2
                    ? "active"
                    : ""
                }`}
              >
                <span className="step-icon">
                  {elapsed > config.total * 0.3 ? "✓" : "○"}
                </span>
                <span className="step-text">Processing your question</span>
              </div>
              <div
                className={`step ${
                  elapsed > config.total * 0.7
                    ? "completed"
                    : elapsed > config.total * 0.3
                    ? "active"
                    : ""
                }`}
              >
                <span className="step-icon">
                  {elapsed > config.total * 0.7 ? "✓" : "○"}
                </span>
                <span className="step-text">Generating responses</span>
              </div>
              <div
                className={`step ${
                  elapsed > config.total * 0.9 ? "active" : ""
                }`}
              >
                <span className="step-icon">○</span>
                <span className="step-text">Finalizing results</span>
              </div>
            </>
          )}
          {type === "scoring" && (
            <>
              <div
                className={`step ${
                  elapsed > 1 ? "completed" : elapsed > 0 ? "active" : ""
                }`}
              >
                <span className="step-icon">{elapsed > 1 ? "✓" : "○"}</span>
                <span className="step-text">Loading medical databases</span>
              </div>
              <div
                className={`step ${
                  elapsed > config.total * 0.4
                    ? "completed"
                    : elapsed > 1
                    ? "active"
                    : ""
                }`}
              >
                <span className="step-icon">
                  {elapsed > config.total * 0.4 ? "✓" : "○"}
                </span>
                <span className="step-text">Analyzing response accuracy</span>
              </div>
              <div
                className={`step ${
                  elapsed > config.total * 0.7
                    ? "completed"
                    : elapsed > config.total * 0.4
                    ? "active"
                    : ""
                }`}
              >
                <span className="step-icon">
                  {elapsed > config.total * 0.7 ? "✓" : "○"}
                </span>
                <span className="step-text">Checking safety criteria</span>
              </div>
              <div
                className={`step ${
                  elapsed > config.total * 0.9 ? "active" : ""
                }`}
              >
                <span className="step-icon">○</span>
                <span className="step-text">Calculating final scores</span>
              </div>
            </>
          )}
        </div>

        <p className="loading-note">
          {type === "generating"
            ? `Testing ${modelCount} model${
                modelCount > 1 ? "s" : ""
              }. This may take a moment...`
            : "Comparing against authoritative medical databases..."}
        </p>
      </div>
    </div>
  );
}

export default LoadingEstimate;
