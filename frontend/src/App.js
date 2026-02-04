import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import Navbar from "./Navbar";
import ScoreChart from "./ScoreChart";
import ScoringTable from "./ScoringTable";
import { useAuth } from "./AuthContext";
import ResetPassword from "./ResetPassword";
import PageGuide from "./PageGuide";

function App() {
  const { token, login } = useAuth();
  const [isResetPassword, setIsResetPassword] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [message, setMessage] = useState("");
  const [selectedModels, setSelectedModels] = useState(["claude"]);
  const [conversationId, setConversationId] = useState(null);
  const [turns, setTurns] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const [isScored, setIsScored] = useState(false);
  const [error, setError] = useState("");
  const [finalSummary, setFinalSummary] = useState(null);
  const [currentRunIndexes, setCurrentRunIndexes] = useState({});
  const [showFloatingButton, setShowFloatingButton] = useState(false);

  // Page guide states
  const [showGuide, setShowGuide] = useState(false);
  const [guidePhase, setGuidePhase] = useState(null);
  const [hasShownResultsGuide, setHasShownResultsGuide] = useState(false);
  const [hasShownScoringGuide, setHasShownScoringGuide] = useState(false);

  // Use ref to track if welcome guide has been checked (prevents re-running)
  const welcomeGuideChecked = useRef(false);

  // Page navigation state
  const [currentPage, setCurrentPage] = useState("input"); // "input" or "results"

  // Helper function to get headers with auth token
  // In the getHeaders() function, check if token exists
  const getHeaders = () => {
    const headers = {
      "Content-Type": "application/json",
    };

    if (token) {
      // ✅ Only add if token exists
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  };

  // ✅ NEW: Handle OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    // Check for reset token
    const urlResetToken = params.get("token");
    if (urlResetToken) {
      setResetToken(urlResetToken);
      setIsResetPassword(true);
      return;
    }

    // Check for OAuth token
    const oauthToken = params.get("oauth_token");
    const oauthEmail = params.get("oauth_email");
    const oauthName = params.get("oauth_name");
    const oauthError = params.get("oauth_error");

    if (oauthError) {
      alert(`Login failed: ${oauthError}`);
      window.history.replaceState({}, "", "/");
      return;
    }

    if (oauthToken && oauthEmail && oauthName) {
      // Log user in with OAuth token
      const user = {
        email: oauthEmail,
        name: oauthName,
      };
      login(oauthToken, user, false); // OAuth users don't need "remember me"

      // Clean URL
      window.history.replaceState({}, "", "/");
    }
  }, [login]);

  useEffect(() => {
    const savedState = sessionStorage.getItem("conversationState");
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setConversationId(parsed.conversationId);
        setTurns(parsed.turns);
        setIsScored(parsed.isScored);
        setFinalSummary(parsed.finalSummary);
        setCurrentRunIndexes(parsed.currentRunIndexes || {});
        setCurrentPage(parsed.currentPage || "input");
        setSelectedModels(parsed.selectedModels || ["claude"]);
        console.log("🔄 Restored conversation state from sessionStorage");
      } catch (err) {
        console.error("Failed to parse saved state:", err);
        sessionStorage.removeItem("conversationState");
      }
    }
  }, []);

  // Show welcome guide on first visit
  useEffect(() => {
    // Only check once per component lifecycle
    if (welcomeGuideChecked.current) {
      return;
    }

    // Check if there's saved state in sessionStorage
    const savedState = sessionStorage.getItem("conversationState");

    if (savedState) {
      // This is a page refresh - show guide based on current page state
      const parsed = JSON.parse(savedState);
      const hasTurns = parsed.turns && parsed.turns.length > 0;
      const isScored = parsed.isScored;
      const page = parsed.currentPage || "input";

      // Determine which guide to show based on page state
      if (page === "results" && hasTurns) {
        // On results page with conversation - show results or scoring guide
        if (isScored && !localStorage.getItem("guide_disabled_scoring")) {
          setTimeout(() => {
            setGuidePhase("scoring");
            setShowGuide(true);
          }, 500);
        } else if (!localStorage.getItem("guide_disabled_results")) {
          setTimeout(() => {
            setGuidePhase("results");
            setShowGuide(true);
          }, 500);
        }
      } else if (
        page === "input" &&
        !localStorage.getItem("guide_disabled_welcome")
      ) {
        // On input page - always show welcome guide (regardless of conversation)
        setTimeout(() => {
          setGuidePhase("welcome");
          setShowGuide(true);
        }, 300);
      }
    } else {
      // First visit - show welcome guide if conditions are met
      const hasSeenWelcome = localStorage.getItem("guide_disabled_welcome");

      if (!hasSeenWelcome && currentPage === "input") {
        setTimeout(() => {
          setGuidePhase("welcome");
          setShowGuide(true);
        }, 300);
      } else {
        setShowGuide(false);
        setGuidePhase(null);
      }
    }

    // Mark as checked so it doesn't run again
    welcomeGuideChecked.current = true;
  }, [currentPage, turns.length]); // Include dependencies to satisfy ESLint

  useEffect(() => {
    // Check URL for reset token
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");

    if (urlToken) {
      setResetToken(urlToken);
      setIsResetPassword(true);
    }
  }, []);

  // Save state to sessionStorage whenever it changes
  useEffect(() => {
    if (conversationId || turns.length > 0) {
      const stateToSave = {
        conversationId,
        turns,
        isScored,
        finalSummary,
        currentRunIndexes,
        currentPage,
        selectedModels,
      };
      sessionStorage.setItem("conversationState", JSON.stringify(stateToSave));
      console.log("💾 Saved conversation state to sessionStorage");
    }
  }, [
    conversationId,
    turns,
    isScored,
    finalSummary,
    currentRunIndexes,
    currentPage,
    selectedModels,
  ]);

  // Detect scroll to show/hide floating button
  useEffect(() => {
    const handleScroll = () => {
      const resultsHeader = document.querySelector(".results-header");
      if (resultsHeader) {
        const rect = resultsHeader.getBoundingClientRect();
        // If header is scrolled out of view, show floating button
        setShowFloatingButton(rect.bottom < 0);
      }
    };

    if (currentPage === "results") {
      window.addEventListener("scroll", handleScroll);
      // Check initial position
      handleScroll();
      return () => window.removeEventListener("scroll", handleScroll);
    }
  }, [currentPage]);

  if (isResetPassword) {
    return (
      <ResetPassword
        token={resetToken}
        onComplete={() => {
          setIsResetPassword(false);
          window.history.replaceState({}, "", "/");
        }}
      />
    );
  }

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) {
      return "Good morning";
    } else if (hour < 18) {
      return "Good afternoon";
    } else {
      return "Good evening";
    }
  };

  // Helper function to get current run index for a turn/model
  const getCurrentRunIndex = (turnNumber, model) => {
    const key = `${turnNumber}-${model}`;
    return currentRunIndexes[key] || 0;
  };

  // Helper function to set current run index for a turn/model
  const setCurrentRunIndex = (turnNumber, model, index) => {
    const key = `${turnNumber}-${model}`;
    setCurrentRunIndexes((prev) => ({
      ...prev,
      [key]: index,
    }));
  };

  // Navigate to previous/next run
  const navigateRun = (turnNumber, model, direction, totalRuns) => {
    const currentIndex = getCurrentRunIndex(turnNumber, model);
    let newIndex = currentIndex + direction;

    // Wrap around
    if (newIndex < 0) {
      newIndex = totalRuns - 1;
    } else if (newIndex >= totalRuns) {
      newIndex = 0;
    }

    setCurrentRunIndex(turnNumber, model, newIndex);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      // ✨ Step 1: Create conversation if needed
      let convId = conversationId;

      if (!convId) {
        console.log("📝 Creating new conversation...");
        const createResponse = await fetch(
          "http://localhost:8000/api/conversations",
          {
            method: "POST",
            headers: getHeaders(), // ← Use auth headers
            body: JSON.stringify({ models: selectedModels }),
          }
        );

        if (!createResponse.ok) {
          throw new Error("Failed to create conversation");
        }

        const createData = await createResponse.json();
        convId = createData.conversation_id;
        setConversationId(convId);
        console.log(`✅ Created conversation ${convId}`);
      }

      // ✨ Step 2: Send message
      console.log(`💬 Sending message to conversation ${convId}...`);
      const response = await fetch(
        `http://localhost:8000/api/conversations/${convId}/send`,
        {
          method: "POST",
          headers: getHeaders(), // ← Use auth headers
          body: JSON.stringify({
            message: message,
            models: selectedModels,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Error: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Received response:", data);
      console.log(
        `🎯 Detected: ${data.prompt_type} (${data.runs_per_model} runs)`
      );

      // ✅ Check for Gemini rate limit errors in responses
      const hasGeminiError = data.responses?.some(
        (r) =>
          r.response_text?.includes("Gemini is overloaded") ||
          r.response_text?.includes("503") ||
          r.response_text?.includes("UNAVAILABLE") ||
          r.response_text?.includes("Error querying Gemini")
      );

      if (hasGeminiError) {
        alert(
          "⚠️ Gemini Rate Limit Hit!\n\n" +
            "Some Gemini responses failed due to rate limiting.\n" +
            "This happens when testing multiple times rapidly.\n\n" +
            "💡 Solution: Wait 1-2 minutes before your next test.\n\n" +
            "Other models (Claude, GPT-5, DeepSeek) completed successfully."
        );
      }

      // ✨ Add to conversation history
      const newTurn = {
        turn_number: data.turn_number,
        user_message: message,
        prompt_type: data.prompt_type,
        runs_per_model: data.runs_per_model,
        responses: {},
        is_scored: false,
      };

      // Group responses by model
      data.responses.forEach((resp) => {
        if (!newTurn.responses[resp.model_name]) {
          newTurn.responses[resp.model_name] = [];
        }
        newTurn.responses[resp.model_name].push({
          run: resp.run_number,
          response: resp.response_text,
          response_time: resp.response_time,
          scored: resp.scored,
          id: resp.id,
        });
      });

      setTurns([...turns, newTurn]);
      setMessage("");

      // ✨ Navigate to results page after receiving responses
      setCurrentPage("results");

      // ✅ Show results guide on first response (if not seen before)
      if (
        !hasShownResultsGuide &&
        !localStorage.getItem("guide_disabled_results")
      ) {
        setTimeout(() => {
          setGuidePhase("results");
          setShowGuide(true);
          setHasShownResultsGuide(true);
        }, 500); // Show quickly after responses load
      }

      // ✅ Auto-scroll to the new turn after it's rendered
      setTimeout(() => {
        const allTurns = document.querySelectorAll(".turn-container");
        if (allTurns.length > 0) {
          const lastTurn = allTurns[allTurns.length - 1];
          lastTurn.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });

          // Auto-expand the new turn's details
          const detailsElements = lastTurn.querySelectorAll(".model-details");
          detailsElements.forEach((details) => {
            details.open = true;
          });
        }
      }, 100);
    } catch (error) {
      console.error("❌ Error:", error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const startScoring = async () => {
    setIsScoring(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:8000/api/conversations/${conversationId}/score`,
        {
          method: "POST",
          headers: getHeaders(), // ← Use auth headers
        }
      );

      if (!response.ok) {
        throw new Error(`Scoring failed: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Scoring result:", data);

      // ✨ Load scores
      await loadScores(conversationId);

      // ⭐ fetch final summary from backend
      const summaryResponse = await fetch(
        `http://localhost:8000/api/conversations/${conversationId}/final-summary`,
        {
          headers: getHeaders(), // ← Use auth headers
        }
      );
      const summaryData = await summaryResponse.json();
      setFinalSummary(summaryData);

      setIsScored(true);

      // ✅ Show scoring guide on first score (if not seen before)
      if (
        !hasShownScoringGuide &&
        !localStorage.getItem("guide_disabled_scoring")
      ) {
        setTimeout(() => {
          setGuidePhase("scoring");
          setShowGuide(true);
          setHasShownScoringGuide(true);
        }, 500); // Show quickly after scoring completes
      }

      // ✨ Scroll to the persistent reminder (scores-above-reminder) after scoring
      setTimeout(() => {
        const scoresReminder = document.querySelector(".scores-above-reminder");
        if (scoresReminder) {
          // Get the element's position
          const elementPosition = scoresReminder.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - 120;

          window.scrollTo({
            top: offsetPosition,
            behavior: "smooth",
          });
        }
      }, 100);
    } catch (error) {
      console.error("❌ Error:", error);
      setError(error.message);
    } finally {
      setIsScoring(false);
    }
  };

  const loadScores = async (convId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/conversations/${convId}/history`,
        {
          headers: getHeaders(), // ← Use auth headers
        }
      );
      const data = await response.json();

      const updatedTurns = data.turns.map((turn) => {
        const responsesByModel = {};

        turn.model_responses.forEach((resp) => {
          const model = resp.model_name;
          if (!responsesByModel[model]) responsesByModel[model] = [];

          responsesByModel[model].push({
            run: responsesByModel[model].length + 1,
            response: resp.response_text,
            scored: resp.scored,
            weighted_score: resp.weighted_score,
            response_time: resp.response_time,
            score_detail: resp.score_data,
            id: resp.id,
          });
        });

        return {
          turn_number: turn.turn_number,
          user_message: turn.user_message,
          responses: responsesByModel,
          is_scored: true,
          prompt_type: data.prompt_type,
          runs_per_model: data.runs_per_model,
        };
      });

      setTurns(updatedTurns);
    } catch (err) {
      console.error("Error loading scores:", err);
    }
  };

  const startNewConversation = () => {
    // Clear state
    setConversationId(null);
    setTurns([]);
    setIsScored(false);
    setMessage("");
    setError("");
    setFinalSummary(null);
    setCurrentRunIndexes({});
    setCurrentPage("input");

    // Clear sessionStorage
    sessionStorage.removeItem("conversationState");

    console.log("🆕 Started new conversation and cleared sessionStorage");
  };

  const goToResultsPage = () => {
    if (turns.length > 0) {
      setCurrentPage("results");
    }
  };

  const continueConversation = () => {
    // Prevent continuing after scoring - user must start new conversation
    if (isScored) {
      return;
    }
    // Allow user to continue before scoring
    setCurrentPage("input");
  };

  const handleNavigation = (section) => {
    console.log(`Navigate to: ${section}`);
  };

  const handleGuideComplete = () => {
    setShowGuide(false);
  };

  // Render Input Page (Page 1)
  const renderInputPage = () => (
    <main className="container page-container">
      <form className="message-form" onSubmit={sendMessage}>
        <h2>{getGreeting()}, how can I help you today?</h2>

        <div className="form-group">
          <textarea
            className="message-textarea"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your medical question... (e.g., 'Is Vioxx safe?')"
            rows={6}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Models to Test:</label>
          <div className="models-container">
            {[
              { id: "claude", name: "Claude" },
              { id: "gpt5", name: "GPT-5" },
              { id: "gemini", name: "Gemini" },
              { id: "deepseek", name: "DeepSeek" },
            ].map((model) => (
              <label key={model.id} className="model-checkbox">
                <input
                  type="checkbox"
                  checked={selectedModels.includes(model.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedModels([...selectedModels, model.id]);
                    } else {
                      setSelectedModels(
                        selectedModels.filter((m) => m !== model.id)
                      );
                    }
                  }}
                />
                <span className="model-name">{model.name}</span>
              </label>
            ))}
          </div>
        </div>

        {error && <div className="error-message">❌ {error}</div>}

        <div className="info-box">
          <div className="info-header">
            <span className="info-icon">💡</span>
            <span>Reminders</span>
          </div>
          <div className="info-content">
            <div className="info-item">
              <div className="info-text">
                Processing time: Each model runs 5 times for reliability (1 time
                for conversations).
                <br />
                <span className="info-subtext">
                  Expected wait: 20-50 seconds depending on models selected.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Button group - either just Send or Send + View Responses */}
        <div className="form-button-group">
          <button
            type="submit"
            className={`btn btn-submit ${isLoading ? "loading" : ""}`}
            disabled={isLoading || !message || selectedModels.length === 0}
          >
            {isLoading ? "⏳ Generating..." : "📤 Send Message"}
          </button>

          {turns.length > 0 && (
            <button
              type="button"
              className="btn btn-view-responses-inline"
              onClick={goToResultsPage}
            >
              📊 View Responses
            </button>
          )}
        </div>
      </form>
    </main>
  );

  // Render Results Page (Page 2)
  const renderResultsPage = () => (
    <main className="container page-container">
      {/* Action Buttons - Redesigned */}
      <div className="results-header">
        <button
          className="btn-back-arrow"
          onClick={continueConversation}
          title={
            isScored
              ? "Scoring complete - start new conversation"
              : "Continue Asking"
          }
          disabled={isScored}
          style={{
            opacity: isScored ? 0.5 : 1,
            cursor: isScored ? "not-allowed" : "pointer",
          }}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
          <span className="back-text">
            {isScored ? "Scoring Complete" : "Continue Asking"}
          </span>
        </button>

        <div className="results-title">
          <h2>Response Analysis</h2>
          <p>
            {turns.length} turn{turns.length > 1 ? "s" : ""} •{" "}
            {Object.keys(turns[0]?.responses || {}).length} model
            {Object.keys(turns[0]?.responses || {}).length > 1 ? "s" : ""}
          </p>
        </div>

        <div className="results-actions">
          <button
            className={`btn-action btn-score-action ${
              isScored ? "scored" : ""
            }`}
            onClick={startScoring}
            disabled={!conversationId || isScoring || isScored}
          >
            {isScoring ? (
              <>
                <span className="spinner"></span>
                Scoring...
              </>
            ) : isScored ? (
              <>Scored</>
            ) : (
              <>Start Scoring</>
            )}
          </button>

          <button
            className="btn-action btn-new-action"
            onClick={startNewConversation}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 5v14M5 12h14"></path>
            </svg>
            New Conversation
          </button>
        </div>
      </div>

      {/* Floating Action Buttons - Shows when scrolled past header */}
      {showFloatingButton && (
        <div className="floating-buttons-container">
          {!isScored && (
            <>
              <button
                className="btn-floating btn-continue-floating"
                onClick={continueConversation}
                title="Continue Asking"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
                Continue Asking
              </button>

              <button
                className="btn-floating btn-score-floating"
                onClick={startScoring}
                disabled={isScoring}
                title="Start Scoring"
              >
                {isScoring ? (
                  <>
                    <span className="spinner-small"></span>
                    Scoring...
                  </>
                ) : (
                  <>
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="12" y1="18" x2="12" y2="12"></line>
                      <line x1="9" y1="15" x2="15" y2="15"></line>
                    </svg>
                    Scoring
                  </>
                )}
              </button>
            </>
          )}

          <button
            className="btn-floating btn-new-floating"
            onClick={startNewConversation}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 5v14M5 12h14"></path>
            </svg>
            New Conversation
          </button>
        </div>
      )}

      {error && <div className="error-message">❌ {error}</div>}

      {/* Conversation History */}
      {turns.length > 0 && (
        <div className="conversation-history">
          <h3>Responses Received</h3>

          {turns.map((turn, idx) => (
            <div key={idx} className="turn-container">
              <div className="turn-header">
                <strong>Turn {turn.turn_number}: </strong>
                {turn.user_message}
                {turn.prompt_type && (
                  <span className="prompt-type-badge">
                    {turn.prompt_type} ({turn.runs_per_model} runs)
                  </span>
                )}
              </div>

              {Object.entries(turn.responses).map(([model, runs]) => {
                const currentIndex = getCurrentRunIndex(
                  turn.turn_number,
                  model
                );
                const currentRun = runs[currentIndex];
                const totalRuns = runs.length;

                return (
                  <div key={model} className="model-response-container">
                    <details className="model-details">
                      <summary className="model-summary">
                        <div className="model-summary-content">
                          <span className="expand-icon">▶</span>
                          <h4 className="model-title-inline">
                            {model.toUpperCase()}
                          </h4>
                          <span className="runs-count">
                            {totalRuns} run{totalRuns > 1 ? "s" : ""}
                          </span>
                        </div>
                        <div className="model-summary-hint">
                          {turn.is_scored
                            ? "Click to expand and see detailed scores and responses"
                            : "Click to expand and see detailed responses"}
                        </div>
                      </summary>

                      <div className="model-content">
                        <div className="run-navigation">
                          <button
                            className="nav-arrow"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigateRun(
                                turn.turn_number,
                                model,
                                -1,
                                totalRuns
                              );
                            }}
                            disabled={totalRuns <= 1}
                            title="Previous run"
                          >
                            <svg
                              width="20"
                              height="20"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <polyline points="15 18 9 12 15 6"></polyline>
                            </svg>
                          </button>

                          <div className="run-info">
                            <span className="run-counter">
                              Run {currentIndex + 1} of {totalRuns}
                            </span>
                            {currentRun.scored &&
                              currentRun.weighted_score !== null && (
                                <span
                                  className={`score-badge ${
                                    currentRun.weighted_score >= 80
                                      ? "high"
                                      : currentRun.weighted_score >= 60
                                      ? "medium"
                                      : "low"
                                  }`}
                                >
                                  Score: {currentRun.weighted_score.toFixed(1)}
                                  /100
                                </span>
                              )}
                            {currentRun.response_time && (
                              <span className="time-badge">
                                {currentRun.response_time.toFixed(2)}s
                              </span>
                            )}
                          </div>

                          <button
                            className="nav-arrow"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigateRun(
                                turn.turn_number,
                                model,
                                1,
                                totalRuns
                              );
                            }}
                            disabled={totalRuns <= 1}
                            title="Next run"
                          >
                            <svg
                              width="20"
                              height="20"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <polyline points="9 18 15 12 9 6"></polyline>
                            </svg>
                          </button>
                        </div>

                        <div className="run-content">
                          {/* ✅ NEW: Show error banner if response contains error */}
                          {(currentRun.response?.includes("Error") ||
                            currentRun.response?.includes("503") ||
                            currentRun.response?.includes("overloaded")) && (
                            <div className="error-banner">
                              <strong>⚠️ This response failed</strong>
                              <p>
                                This usually happens due to API rate limits.
                                Wait 1-2 minutes and try again.
                              </p>
                            </div>
                          )}

                          {currentRun.scored && currentRun.score_detail ? (
                            <div className="score-details">
                              <ScoringTable
                                scoreDetail={currentRun.score_detail}
                              />

                              <details className="run-detail-nested">
                                <summary>
                                  📄 Click to View Original Response
                                </summary>
                                <div className="response-text">
                                  {currentRun.response}
                                </div>
                              </details>
                            </div>
                          ) : currentRun.scored && !currentRun.score_detail ? (
                            <div>
                              <div className="info-message">
                                ℹ️ Scoring completed but detailed breakdown is
                                not available for this response.
                              </div>
                              <div className="response-text">
                                {currentRun.response}
                              </div>
                            </div>
                          ) : (
                            <div>
                              <div className="info-message">
                                💡 Click "Start Scoring" button above to see
                                detailed scoring breakdown.
                              </div>
                              <div className="response-text">
                                {currentRun.response}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </details>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}

      {/* Recommendation Section */}
      {finalSummary && (
        <div id="recommendation-section" className="recommendation-section">
          {/* Persistent reminder - always visible */}
          <div className="scores-above-reminder">
            <span>View detailed scores for each response above</span>
            <button
              className="scroll-to-scores-btn"
              onClick={() => {
                // Scroll to conversation history
                const historyElement = document.querySelector(
                  ".conversation-history"
                );
                if (historyElement) {
                  const elementPosition =
                    historyElement.getBoundingClientRect().top;
                  const offsetPosition =
                    elementPosition + window.pageYOffset - 100;

                  window.scrollTo({
                    top: offsetPosition,
                    behavior: "smooth",
                  });

                  // Expand all model details after scrolling
                  setTimeout(() => {
                    const allDetails =
                      document.querySelectorAll(".model-details");
                    allDetails.forEach((details) => {
                      details.open = true;
                    });
                  }, 500); // Wait for scroll to complete
                }
              }}
            >
              Click to See Detailed Scores
            </button>
          </div>

          <ScoreChart summary={finalSummary} turns={turns} />
        </div>
      )}
    </main>
  );

  return (
    <div className="App">
      <Navbar onNavigate={handleNavigation} />

      {currentPage === "input" ? renderInputPage() : renderResultsPage()}

      {/* Page Guide Tutorial */}
      {showGuide && guidePhase && (
        <PageGuide phase={guidePhase} onComplete={handleGuideComplete} />
      )}
    </div>
  );
}

export default App;
