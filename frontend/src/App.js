import React, { useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [selectedModels, setSelectedModels] = useState([
    "gpt5",
    "claude",
    "gemini",
    "deepseek",
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [responses, setResponses] = useState(null);
  const [error, setError] = useState("");

  const NUM_RUNS = 25;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setResponses(null);

    try {
      console.log("Sending request to backend...");
      console.log("Request data:", { question, models: selectedModels });

      const response = await fetch("http://localhost:8000/api/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          models: selectedModels,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || `Backend error: ${response.status}`
        );
      }

      const data = await response.json();

      // ✅ DETAILED DEBUGGING
      console.log("=== RESPONSE DEBUG ===");
      console.log("Full data:", data);
      console.log("Has responses?:", !!data.responses);
      console.log(
        "Response keys:",
        data.responses ? Object.keys(data.responses) : "none"
      );

      if (data.responses) {
        Object.keys(data.responses).forEach((model) => {
          console.log(`${model}:`, data.responses[model]);
        });
      }
      console.log("=== END DEBUG ===");

      setResponses(data);

      // Check state after setting
      setTimeout(() => {
        console.log("State updated, responses is now:", data);
      }, 100);
    } catch (error) {
      console.error("Error:", error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏥 Medical LLM Safety Benchmark</h1>
        <p>Test multiple LLMs on medical questions (25 runs per model)</p>
      </header>

      <main className="container">
        <form onSubmit={handleSubmit} className="input-form">
          <h2>Ask a Medical Question</h2>

          <div className="form-group">
            <label>Your Question:</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What is diabetes? / Is aspirin safe? / I have chest pain, what should I do?"
              rows={3}
              required
            />
          </div>

          <div className="form-group">
            <label>Models to Test:</label>
            <div className="checkbox-group">
              {[
                { id: "gpt5", name: " GPT-5" },
                { id: "claude", name: " Claude" },
                { id: "gemini", name: " Gemini" },
                { id: "deepseek", name: " DeepSeek" },
              ].map((model) => (
                <label key={model.id} className="checkbox-label">
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
                  {model.name}
                </label>
              ))}
            </div>
          </div>

          <div className="info-box">
            <p>
              ℹ️ Each model will be tested <strong>25 times</strong> for
              statistical reliability
            </p>
            <p>
              Total API calls: {selectedModels.length} models × 25 runs ={" "}
              <strong>{selectedModels.length * 25}</strong>
            </p>
            <p>
              Estimated time: ~{Math.ceil((selectedModels.length * 25) / 10)}{" "}
              minutes
            </p>
          </div>

          <button
            type="submit"
            disabled={isLoading || !question || selectedModels.length === 0}
          >
            {isLoading
              ? "🔄 Testing... Please wait"
              : `🚀 Start Testing (${
                  selectedModels.length * NUM_RUNS
                } API calls)`}
          </button>

          {isLoading && (
            <div className="loading-info">
              <p>⏳ Running {selectedModels.length * NUM_RUNS} tests...</p>
              <p>
                This will take approximately{" "}
                {Math.ceil((selectedModels.length * NUM_RUNS) / 10)} minutes.
              </p>
              <p>Please don't close this window!</p>
            </div>
          )}
        </form>

        {error && (
          <div className="error-box">
            <h3>❌ Error</h3>
            <p>{error}</p>
            <small>Make sure backend is running on http://localhost:8000</small>
          </div>
        )}

        {responses && (
          <div className="results">
            <h2>✅ Results</h2>

            <div className="info-section">
              <p>
                <strong>Question:</strong> {responses.question}
              </p>
              <p>
                <strong>Models Tested:</strong>{" "}
                {responses.models_tested?.join(", ")}
              </p>
              <p>
                <strong>Runs per Model:</strong> {responses.num_runs}
              </p>
              <p>
                <strong>Total Tests:</strong>{" "}
                {responses.models_tested?.length * responses.num_runs}
              </p>
            </div>

            <div className="responses-section">
              {responses.responses &&
                Object.entries(responses.responses).map(([model, runs]) => (
                  <div key={model} className="model-response">
                    <h3>{model.toUpperCase()}</h3>
                    <p className="run-summary">{runs.length} runs completed</p>

                    {runs.slice(0, 3).map((run, idx) => (
                      <details
                        key={idx}
                        className="run-detail"
                        open={idx === 0}
                      >
                        <summary>Run {run.run}</summary>
                        <div className="response-text">{run.response}</div>
                      </details>
                    ))}

                    {runs.length > 3 && (
                      <details className="run-detail">
                        <summary>View all {runs.length} runs...</summary>
                        <div className="all-runs">
                          {runs.slice(3).map((run, idx) => (
                            <details
                              key={idx + 3}
                              className="run-detail-nested"
                            >
                              <summary>Run {run.run}</summary>
                              <div className="response-text">
                                {run.response}
                              </div>
                            </details>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
