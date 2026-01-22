import React from "react";
import "./ScoringTable.css";

const ScoringTable = ({ scoreDetail }) => {
  if (!scoreDetail) {
    return (
      <div className="scoring-details-container">
        <div className="scoring-unavailable">
          <span className="unavailable-icon">ℹ️</span>
          <p>Scoring details are not available for this response.</p>
        </div>
      </div>
    );
  }

  if (!scoreDetail.raw_scores) {
    return (
      <div className="scoring-details-container">
        <div className="scoring-unavailable">
          <span className="unavailable-icon">⚠️</span>
          <p>Scoring was attempted but detailed scores are missing.</p>
        </div>
      </div>
    );
  }

  const { raw_scores } = scoreDetail;

  // Helper function to format category names
  const formatCategoryName = (key) => {
    return key
      .replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Helper function to get row class based on score
  const getRowClass = (score) => {
    if (score === 0) return "score-perfect";
    if (score >= 0.5) return "score-poor";
    return "score-medium";
  };

  // Helper function to get icon based on score
  const getScoreIcon = (score) => {
    if (score === 0) return "✅";
    if (score >= 0.5) return "❌";
    return "⚠️";
  };

  // Extract all categories except reasoning
  const categories = Object.entries(raw_scores).filter(
    ([key]) => key !== "reasoning"
  );

  // Sort categories: worst scores first
  const sortedCategories = categories.sort((a, b) => b[1] - a[1]);

  return (
    <div className="scoring-details-container">
      <h5 className="scoring-title">📊 Scoring Details</h5>
      <p className="scoring-subtitle">Category Scores (0 = Best, 1 = Worst):</p>

      <div className="scoring-table">
        <div className="table-header">
          <div className="col-category">Category</div>
          <div className="col-score">Score</div>
          <div className="col-explanation">Explanation</div>
        </div>

        {sortedCategories.map(([category, score]) => {
          // Extract explanation for this category from reasoning
          const reasoning = raw_scores.reasoning || "";

          // Try multiple patterns to extract category-specific explanation
          const formattedCategory = formatCategoryName(category);

          // Pattern 1: "Category (score): explanation." or "Category (score) explanation."
          let pattern = new RegExp(
            `${formattedCategory}\\s*\\([^)]*\\)[:\\s-]*([^.]+\\.?)`,
            "i"
          );
          let match = reasoning.match(pattern);

          // Pattern 2: "Category: explanation" or "Category - explanation"
          if (!match) {
            pattern = new RegExp(
              `${formattedCategory}\\s*[:-]\\s*([^.]+\\.?)`,
              "i"
            );
            match = reasoning.match(pattern);
          }

          // Pattern 3: Look for "For category" pattern
          if (!match) {
            pattern = new RegExp(
              `For\\s+${formattedCategory.toLowerCase()}\\s*\\([^)]*\\)[,:]?\\s*([^.]+\\.?)`,
              "i"
            );
            match = reasoning.match(pattern);
          }

          // Pattern 4: Find sentence containing the category name
          if (!match) {
            const sentences = reasoning.split(/\.\s+/);
            const relevantSentence = sentences.find((s) =>
              s
                .toLowerCase()
                .includes(category.replace(/_/g, " ").toLowerCase())
            );
            if (relevantSentence) {
              // Clean up the sentence - remove the category name prefix if present
              let cleaned = relevantSentence.trim();
              const prefixPattern = new RegExp(
                `^.*?${formattedCategory}\\s*\\([^)]*\\)[:\\s-]*`,
                "i"
              );
              cleaned = cleaned.replace(prefixPattern, "");
              match = [null, cleaned + "."];
            }
          }

          const explanation =
            match && match[1]
              ? match[1].trim()
              : "No specific explanation provided";

          return (
            <div key={category} className={`table-row ${getRowClass(score)}`}>
              <div className="col-category">
                <span className="category-icon">{getScoreIcon(score)}</span>
                <span className="category-name">
                  {formatCategoryName(category)}
                </span>
              </div>
              <div className="col-score">
                <span className="score-badge">{score}</span>
              </div>
              <div className="col-explanation">{explanation}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ScoringTable;
