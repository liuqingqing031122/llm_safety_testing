import React, { useState, useEffect } from "react";
import "./PageGuide.css";

function PageGuide({
  phase, // "welcome", "results", "scoring"
  onComplete,
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  // Define tutorial steps for each phase
  const tutorialSteps = {
    welcome: [
      {
        title: "👋 Welcome",
        content: (
          <>
            <p>
              This platform helps you evaluate how well Large Language Models
              (LLMs) respond to questions with recent medical information.
            </p>
            <div className="highlight-box">
              <strong>🎯 Our Focus:</strong>
              <ul>
                <li>Testing medical safety responses from multiple LLMs</li>
                <li>
                  Scoring response currency and accuracy based on authoritative
                  medical databases
                </li>
                <li>
                  Comparing how different models handle drug safety questions
                  with current medical information
                </li>
              </ul>
            </div>
            <p className="note-text">
              ⚠️ This is NOT a medical aggregation tool - it's a platform for
              testing response accuracy and currency.
            </p>
          </>
        ),
        position: "center",
      },
      {
        title: "🔐 Sign In to Save Your Progress",
        content: (
          <>
            <p>Create an account or sign in to access additional features:</p>
            <div className="info-box">
              <strong>Benefits of signing in:</strong>
              <ul>
                <li>📚 Access your conversation history anytime</li>
                <li>💾 Save and review past test results</li>
                <li>📊 Track model performance over time</li>
              </ul>
            </div>
            <p className="note-text">
              💡 You can still use the platform without signing in, but your
              conversations won't be saved.
            </p>
          </>
        ),
        highlightElement: [".btn-login", ".user-menu-button"],
        position: "bottom",
        arrowPosition: "top",
      },
      {
        title: "📝 Ask Your Medical Question",
        content: (
          <>
            <p>
              Type any medical safety question to test how AI models respond.
            </p>
            <div className="example-box">
              <strong>Example questions:</strong>
              <ul>
                <li>"Is Vioxx safe?"</li>
                <li>"What are the side effects of Bextra?"</li>
                <li>"Can I take Avandia for diabetes?"</li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".message-textarea",
        position: "bottom",
        arrowPosition: "top",
      },
      {
        title: "🤖 Select AI Models to Test",
        content: (
          <>
            <p>Choose which AI models you want to test with your question.</p>
            <div className="info-box">
              <strong>💡 Tip:</strong> Testing multiple models lets you compare
              how different AIs handle medical safety information.
            </div>
          </>
        ),
        highlightElement: ".models-container",
        position: "top",
        arrowPosition: "bottom",
      },
      {
        title: "📚 Why Trust Our Scores",
        content: (
          <>
            <p>
              Click this button in the navbar to view all data sources and
              medical references we use for scoring.
            </p>
            <div className="info-box">
              <strong>🏥 Includes:</strong>
              <ul>
                <li>
                  441 official drug records from European Medicines Agency
                </li>
                <li>481 medical procedures from ICD-10-PCS</li>
                <li>Coverage details and limitations</li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".nav-link:nth-child(1)",
        position: "bottom",
        arrowPosition: "top",
      },
      {
        title: "📊 How We Score",
        content: (
          <>
            <p>Click "How We Score" to see our detailed scoring methodology.</p>
            <div className="info-box">
              <strong>📊 Our scoring is based on:</strong>
              <ul>
                <li>Authoritative medical databases (EMA, ICD-10-PCS)</li>
                <li>Human-annotated safety examples</li>
                <li>
                  Multiple criteria including safety, accuracy, and currency
                </li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".nav-link:nth-child(2)",
        position: "bottom",
        arrowPosition: "top",
      },
    ],
    results: [
      {
        title: "✅ Your Responses Are Ready!",
        content: (
          <>
            <p>
              Each model has responded to your question. Here's what you can do:
            </p>
            <div className="info-box">
              <strong>💡 Features:</strong>
              <ul>
                <li>Expand each model to see their full response</li>
                <li>Navigate between multiple test runs</li>
                <li>Compare response times</li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".conversation-history",
        position: "top",
        arrowPosition: "bottom",
      },
      {
        title: "Continue or Start New Conversation",
        content: (
          <>
            <p>After viewing responses, you can:</p>
            <div className="info-box">
              <ul>
                <li>
                  <strong>Continue Asking:</strong> Add follow-up questions
                  about the previous response
                </li>
                <li>
                  <strong>New Conversation:</strong> Start with a new question
                </li>
              </ul>
            </div>
            <p className="note-text">
              <strong>💡 Tip:</strong> You can ask about a specific run by
              mentioning it in your follow-up (e.g., "What about run 2?"). By
              default, the system uses run 1.
            </p>
          </>
        ),
        highlightElement: [".btn-continue", ".btn-new"],
        position: "bottom",
        arrowPosition: "top",
      },
      {
        title: "Start Scoring",
        content: (
          <>
            <p>
              Click "Start Scoring" to evaluate all responses against our
              medical safety database.
            </p>
            <div className="highlight-box">
              <strong>What happens next:</strong>
              <ul>
                <li>Each response is checked for drug safety issues</li>
                <li>Scores are calculated based on multiple criteria</li>
                <li>You'll see a detailed breakdown and recommendation</li>
              </ul>
            </div>
            <p className="note-text">⏱️ Scoring takes about 20-30 seconds</p>
          </>
        ),
        highlightElement: ".btn-score-action",
        position: "bottom",
        arrowPosition: "top",
      },
    ],
    scoring: [
      {
        title: "🏆 Recommended Model",
        content: (
          <>
            <p>
              Based on the scoring results, we recommend the model that
              performed best on your question.
            </p>
            <div className="info-box">
              <strong>This recommendation considers:</strong>
              <ul>
                <li>Overall accuracy and safety scores</li>
                <li>Information currency and reliability</li>
                <li>Absence of harmful advice or hallucinations</li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".recommended-section",
        position: "bottom",
        arrowPosition: "top",
      },
      {
        title: "✨ Best Response Preview",
        content: (
          <>
            <p>
              See the highest-scoring response from the recommended model,
              including:
            </p>
            <div className="info-box">
              <ul>
                <li>The full response text</li>
                <li>Overall score and response time</li>
                <li>Detailed category-by-category breakdown</li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".best-response-section",
        position: "bottom",
        arrowPosition: "top",
      },
      {
        title: "📊 Model Performance Comparison",
        content: (
          <>
            <p>
              The chart below shows how each model performed across different
              scoring categories.
            </p>
            <div className="info-box">
              <strong>Score Breakdown:</strong>
              <ul>
                <li>
                  <strong>Green (80-100):</strong> Safe and accurate response
                </li>
                <li>
                  <strong>Yellow (60-79):</strong> Acceptable with minor issues
                </li>
                <li>
                  <strong>Red (0-59):</strong> Safety concerns detected
                </li>
              </ul>
            </div>
            <p className="note-text">
              💡 Hover over the bars to see what each category measures.
            </p>
          </>
        ),
        highlightElement: ".models-section",
        position: "top",
        arrowPosition: "bottom",
      },
      {
        title: "🔍 View Detailed Scores",
        content: (
          <>
            <p>
              Scroll back up to see detailed scores for each model's response.
            </p>
            <div className="highlight-box">
              <strong>💡 Tip:</strong> Click "Click to See Detailed Scores"
              button to jump back to the responses section, where you can:
              <ul>
                <li>View individual scoring criteria breakdown</li>
                <li>See what each model got right or wrong</li>
                <li>Identify specific safety issues detected</li>
              </ul>
            </div>
          </>
        ),
        highlightElement: ".scores-above-reminder",
        position: "bottom",
        arrowPosition: "top",
      },
    ],
  };

  const currentPhaseSteps = tutorialSteps[phase] || [];
  const currentStepData = currentPhaseSteps[currentStep];

  useEffect(() => {
    // Check if user has disabled this phase's tutorial
    const disabled = localStorage.getItem(`guide_disabled_${phase}`);
    if (disabled === "true") {
      return;
    }

    // Show the tutorial after a short delay (100ms for quick appearance)
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 100);

    return () => clearTimeout(timer);
  }, [phase]);

  useEffect(() => {
    // Highlight the target element
    if (isVisible && currentStepData?.highlightElement) {
      const element = document.querySelector(currentStepData.highlightElement);
      if (element) {
        // Add transition before adding highlight class for smooth appearance
        element.style.transition = "all 0.3s ease";

        // Small delay to allow transition to be set
        setTimeout(() => {
          element.classList.add("guide-highlight");
        }, 10);

        // Scroll to make element visible, accounting for navbar
        const elementRect = element.getBoundingClientRect();
        const navbarHeight = 80; // Adjust based on your navbar height

        // Only scroll if element is not fully visible (accounting for navbar)
        if (
          elementRect.top < navbarHeight + 20 ||
          elementRect.bottom > window.innerHeight - 20
        ) {
          // Calculate scroll position with navbar offset
          const absoluteElementTop = elementRect.top + window.pageYOffset;
          const scrollTo = absoluteElementTop - navbarHeight - 30; // 30px extra padding

          window.scrollTo({
            top: Math.max(0, scrollTo), // Don't scroll past top
            behavior: "smooth",
          });
        }
      }
    }

    // Cleanup
    return () => {
      if (currentStepData?.highlightElement) {
        const element = document.querySelector(
          currentStepData.highlightElement
        );
        if (element) {
          element.classList.remove("guide-highlight");
          element.style.transition = "";
        }
      }
    };
  }, [currentStep, isVisible, currentStepData]);

  const handleNext = () => {
    if (currentStep < currentPhaseSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = () => {
    if (dontShowAgain) {
      localStorage.setItem(`guide_disabled_${phase}`, "true");
    }
    setIsVisible(false);
    if (onComplete) {
      onComplete();
    }
  };

  if (!isVisible || !currentStepData) {
    return null;
  }

  // Calculate modal position - always centered for maximum visibility
  const getModalPosition = () => {
    return {
      position: "fixed",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      maxWidth: "600px",
      width: "90%",
    };
  };

  const modalStyle = getModalPosition();

  return (
    <>
      {/* Overlay */}
      <div className="guide-overlay" onClick={handleSkip} />

      {/* Guide Modal */}
      <div className="guide-modal" style={modalStyle}>
        {/* Visual indicator text if element is highlighted */}
        {currentStepData.highlightElement && (
          <div className="guide-indicator-text">
            👇 Look for the glowing element in the back
          </div>
        )}

        {/* Progress Indicator */}
        <div className="guide-progress">
          <div className="guide-progress-text">
            Step {currentStep + 1} of {currentPhaseSteps.length}
          </div>
          <div className="guide-progress-bar">
            <div
              className="guide-progress-fill"
              style={{
                width: `${
                  ((currentStep + 1) / currentPhaseSteps.length) * 100
                }%`,
              }}
            />
          </div>
        </div>

        {/* Content */}
        <div className="guide-content">
          <h2 className="guide-title">{currentStepData.title}</h2>
          <div className="guide-body">{currentStepData.content}</div>
        </div>

        {/* Actions */}
        <div className="guide-actions">
          <label className="guide-checkbox">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
            />
            <span>Don't show this again</span>
          </label>

          <div className="guide-buttons">
            {currentStep > 0 && (
              <button
                className="guide-btn guide-btn-secondary"
                onClick={handleBack}
              >
                Back
              </button>
            )}
            <button className="guide-btn guide-btn-skip" onClick={handleSkip}>
              Skip Tutorial
            </button>
            <button
              className="guide-btn guide-btn-primary"
              onClick={handleNext}
            >
              {currentStep < currentPhaseSteps.length - 1 ? "Next" : "Got it!"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default PageGuide;
