import React, { useState } from "react";
import "./App.css";
import ScoreChart from "./ScoreChart";

function App() {
  const [message, setMessage] = useState("");
  const [selectedModels, setSelectedModels] = useState(["claude"]);
  const [conversationId, setConversationId] = useState(null);
  const [turns, setTurns] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const [isScored, setIsScored] = useState(false);
  const [error, setError] = useState("");
  const [finalSummary, setFinalSummary] = useState(null);

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
          "https://medical-llm-backend-production.up.railway.app/api/conversations",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
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
        `https://medical-llm-backend-production.up.railway.app/api/conversations/${convId}/send`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
    } catch (error) {
      console.error("❌ Error:", error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const startScoring = async () => {
    if (!conversationId) {
      alert("No conversation to score!");
      return;
    }

    setIsScoring(true);
    setError("");

    try {
      const response = await fetch(
        `https://medical-llm-backend-production.up.railway.app/api/conversations/${conversationId}/score`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!response.ok) {
        throw new Error(`Scoring failed: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Scoring result:", data);

      alert(
        `✅ Scoring complete!\n` +
          `Scored: ${data.scored_count}/${data.total_responses} responses\n` +
          (data.errors ? `Errors: ${data.errors.length}` : "")
      );

      // ✨ Load scores
      await loadScores(conversationId);

      // ⭐ fetch final summary from backend
      const summaryResponse = await fetch(
        `https://medical-llm-backend-production.up.railway.app/api/conversations/${conversationId}/final-summary`
      );
      const summaryData = await summaryResponse.json();
      setFinalSummary(summaryData);

      setIsScored(true);
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
        `https://medical-llm-backend-production.up.railway.app/api/conversations/${convId}/history`
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
    setConversationId(null);
    setTurns([]);
    setIsScored(false);
    setMessage("");
    setError("");
    setFinalSummary(null);
    console.log("🆕 Started new conversation");
  };

  // Helper function to format score category names
  const formatCategoryName = (key) => {
    return key
      .replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Helper function to get score color class
  const getScoreColorClass = (value) => {
    if (value === 0) return "perfect";
    if (value === 1) return "poor";
    return "medium";
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏥 Medical LLM Safety Benchmark</h1>
        <p>Multi-turn conversations with automated safety scoring</p>

        <div className="button-container">
          <button className="btn btn-new" onClick={startNewConversation}>
            🆕 New Conversation
          </button>

          <button
            className={`btn btn-score ${isScored ? "scored" : ""}`}
            onClick={startScoring}
            disabled={!conversationId || isScoring || isScored}
          >
            {isScoring
              ? "⏳ Scoring..."
              : isScored
              ? "✅ Scored"
              : "📊 Start Scoring"}
          </button>
        </div>
      </header>

      <main className="container">
        {/* Message Input Form */}
        <form className="message-form" onSubmit={sendMessage}>
          <h2>Send Message</h2>

          <div className="form-group">
            <label className="form-label">Your Message:</label>
            <textarea
              className="message-textarea"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your medical question... (e.g., 'Is Vioxx safe?')"
              rows={3}
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

          <button
            type="submit"
            className={`btn btn-submit ${isLoading ? "loading" : ""}`}
            disabled={isLoading || !message || selectedModels.length === 0}
          >
            {isLoading ? "⏳ Generating..." : "📤 Send Message"}
          </button>

          <div className="notice-box">
            <div className="notice-header">
              <span className="notice-icon">⚠️</span>
              <span>IMPORTANT NOTICE</span>
            </div>
            <ul className="notice-content">
              <li>
                Please click 'New Conversation' every time you ask a new
                question (or keep asking if you want to follow up on the
                previous question, and the system will automatically change into
                conversational mode).
              </li>
              <li>
                System will automatically run 5 times per model for stability
                (or 1 time for conversational prompts). Each model might take
                about 2-5 minutes to generate responses, please wait patiently.
                NOTE: GPT-5 might take up to 10 minutes to run.
              </li>
            </ul>
          </div>
        </form>

        {/* Conversation History */}
        {turns.length > 0 && (
          <div className="conversation-history">
            <h3>Conversation History</h3>

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

                {Object.entries(turn.responses).map(([model, runs]) => (
                  <div key={model} className="model-response-container">
                    <h4 className="model-title">{model.toUpperCase()}</h4>

                    {runs.map((run, runIdx) => (
                      <details key={runIdx} className="run-details">
                        <summary className="run-summary">
                          <div className="run-summary-main">
                            <span className="run-number">Run {run.run}</span>
                            {run.scored && run.weighted_score !== null && (
                              <span
                                className={`score-badge ${
                                  run.weighted_score >= 80
                                    ? "high"
                                    : run.weighted_score >= 60
                                    ? "medium"
                                    : "low"
                                }`}
                              >
                                Score: {run.weighted_score.toFixed(1)}/100
                              </span>
                            )}
                            {run.response_time && (
                              <span className="time-badge">
                                {run.response_time.toFixed(2)}s
                              </span>
                            )}
                          </div>
                          <div className="expand-hint">
                            {run.scored && run.score_detail
                              ? "Click to view detailed scoring and original response"
                              : "Click to view response"}
                          </div>
                        </summary>

                        <div className="run-content">
                          {/* ✨ Show score details if scored, otherwise show response */}
                          {run.scored && run.score_detail ? (
                            <div className="score-details">
                              <h5>📊 Scoring Details</h5>

                              {/* Display score categories */}
                              <div className="raw-scores">
                                <strong>
                                  Category Scores (0 = Best, 1 = Worst):
                                </strong>
                                <ul>
                                  {Object.entries(
                                    run.score_detail.raw_scores || {}
                                  ).map(([key, value]) => {
                                    if (key === "reasoning") return null;
                                    return (
                                      <li key={key}>
                                        <span className="score-label">
                                          {formatCategoryName(key)}:
                                        </span>
                                        <span
                                          className={`score-value ${getScoreColorClass(
                                            value
                                          )}`}
                                        >
                                          {value}
                                        </span>
                                      </li>
                                    );
                                  })}
                                </ul>
                              </div>

                              {/* ✨ Display scoring reasoning */}
                              {run.score_detail.raw_scores?.reasoning && (
                                <div className="score-reasoning">
                                  <strong>💡 Scoring Reasoning:</strong>
                                  <p>{run.score_detail.raw_scores.reasoning}</p>
                                </div>
                              )}

                              {/* Display critical issues if any */}
                              {run.score_detail.reference_checks
                                ?.withdrawn_drugs?.has_issues && (
                                <div className="warning-box">
                                  <strong>⚠️ Critical Issues Detected:</strong>
                                  <ul>
                                    {run.score_detail.reference_checks.withdrawn_drugs.issues.map(
                                      (issue, idx) => (
                                        <li key={idx}>
                                          Mentions withdrawn drug:{" "}
                                          <strong>{issue.drug_name}</strong>
                                          {issue.withdrawal_date &&
                                            ` (withdrawn ${issue.withdrawal_date})`}
                                        </li>
                                      )
                                    )}
                                  </ul>
                                </div>
                              )}

                              {/* Show original response in a collapsible section */}
                              <details className="run-detail-nested">
                                <summary>📄 View Original Response</summary>
                                <div className="response-text">
                                  {run.response}
                                </div>
                              </details>
                            </div>
                          ) : (
                            /* Show response text if not scored yet */
                            <div className="response-text">{run.response}</div>
                          )}
                        </div>
                      </details>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {finalSummary && <ScoreChart summary={finalSummary} />}

        {turns.length === 0 && (
          <div className="empty-state">
            <p>👋 No conversation yet. Send a message to get started!</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
