import React, { useState, useEffect } from "react";
import "./References.css";

function ReferencesSection() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch reference statistics from backend
    fetch("http://localhost:8000/api/references/stats")
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load reference stats:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="references-section">
      {/* Collapsed Header - Always Visible */}
      <div
        className="references-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="references-title">
          <span className="icon">📚</span>
          <span className="title-text">
            {loading ? (
              "Loading reference data..."
            ) : stats ? (
              <>Why You Can Trust Our Scores - Expand to View Sources</>
            ) : (
              "Data Sources & Methodology"
            )}
          </span>
        </div>
        <button className="expand-btn" aria-label="Toggle references">
          {isExpanded ? "▲" : "▼"}
        </button>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="references-content">
          <div className="references-grid">
            {/* Medical References Section */}
            <div className="reference-card">
              <h3>🏥 Medical References</h3>

              <div className="reference-item">
                <h4>EMA Defined Drugs Status</h4>
                <p className="reference-description">
                  European Medicines Agency database of all medicines includes
                  approved, expired, withdrawn, etc.
                </p>
                <ul className="reference-details">
                  <li>
                    <strong>Entries:</strong>{" "}
                    {stats?.withdrawn_drugs_count || "Loading..."} drugs
                  </li>
                  <li>
                    <strong>Source:</strong> European Medicines Agency (EMA)
                  </li>
                  <li>
                    <strong>File:</strong> medicines_output_medicines_en.xlsx
                  </li>
                  <li>
                    <strong>Link:</strong>{" "}
                    <a
                      href="https://www.ema.europa.eu/en/documents/report/medicines-output-medicines-report_en.xlsx"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      EMA MEDICINES DATA TABLE
                    </a>
                  </li>
                </ul>
              </div>

              <div className="reference-item">
                <h4>ICD-10-PCS Medical Procedures</h4>
                <p className="reference-description">
                  International Classification of Diseases, 10th Revision,
                  Procedure Coding System - common medical procedures database.
                </p>
                <ul className="reference-details">
                  <li>
                    <strong>Entries:</strong>{" "}
                    {stats?.common_procedures_count || "Loading..."} procedures
                  </li>
                  <li>
                    <strong>Categories:</strong>{" "}
                    {stats?.procedure_categories || "7"} specialties (Cardiac,
                    Orthopedic, GI, etc.)
                  </li>
                  <li>
                    <strong>Source:</strong> Centers for Medicare & Medicaid
                    Services (CMS)
                  </li>
                  <li>
                    <strong>File:</strong> icd10pcs_order_2026.txt
                  </li>
                  <li>
                    <strong>Link:</strong>{" "}
                    <a
                      href="https://www.cms.gov/medicare/coding-billing/icd-10-codes"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      ICD-10 FILES
                    </a>
                  </li>
                </ul>
              </div>
            </div>

            {/* Scoring Methodology Section */}
            <div className="reference-card">
              <h3>📊 Scoring Methodology</h3>

              <div className="reference-item">
                <h4>Few-Shot Examples</h4>
                <p className="reference-description">
                  Human-annotated examples used to calibrate the AI scoring
                  system across different prompt types.
                </p>
                <ul className="reference-details">
                  <li>
                    <strong>Direct Prompts:</strong>{" "}
                    {stats?.direct_examples || "0"} examples
                  </li>
                  <li>
                    <strong>Indirect Prompts:</strong>{" "}
                    {stats?.indirect_examples || "0"} examples
                  </li>
                  <li>
                    <strong>Conversational:</strong>{" "}
                    {stats?.conversational_examples || "0"} examples
                  </li>
                  <li>
                    <strong>Source:</strong>Human scoring safety annotations
                  </li>
                </ul>
              </div>

              <div className="methodology-box">
                <h4>How We Use These References</h4>
                <ol>
                  <li>
                    <strong>Drug Safety Check:</strong> Every model response is
                    scanned for mentions of drugs in the EMA withdrawn database
                  </li>
                  <li>
                    <strong>Procedure Validation:</strong> Medical procedures
                    are verified against ICD-10-PCS standard terminology
                  </li>
                  <li>
                    <strong>Scoring Calibration:</strong> Few-shot examples
                    ensure consistent scoring across different prompt types
                  </li>
                </ol>
              </div>
            </div>

            {/* Coverage & Limitations Section */}
            <div className="reference-card limitations-card">
              <h3>⚠️ Coverage & Limitations</h3>

              <div className="limitation-section">
                <h4>✅ What's Covered</h4>
                <ul>
                  <li>European drug safety data (EMA)</li>
                  <li>
                    International standard medical procedures (ICD-10-PCS)
                  </li>
                  <li>Withdrawn, refused, suspended, and revoked medicines</li>
                </ul>
              </div>

              <div className="limitation-section">
                <h4>❌ What's NOT Covered</h4>
                <ul>
                  <li>US FDA-specific data (partial overlap with EMA)</li>
                  <li>Asian/African regulatory databases</li>
                  <li>Dietary supplements and herbal medicines</li>
                  <li>Over-the-counter medication safety data</li>
                  <li>Drug interactions and contraindications</li>
                </ul>
              </div>

              <div className="disclaimer">
                <strong>Medical Disclaimer:</strong> This system is for research
                and benchmarking purposes only. It is NOT a substitute for
                professional medical advice, diagnosis, or treatment. Always
                consult qualified healthcare providers for medical decisions.
              </div>
            </div>

            {/* Last Updated Section */}
            <div className="reference-card update-card">
              <h3>🔄 Data Currency</h3>
              <p>
                <strong>Last Updated:</strong> January 2026
              </p>
              <p>
                <strong>Update Frequency:</strong> Reference databases are
                updated based on the official organisation updates.
              </p>
              <p className="update-note">
                ℹ️ If you notice outdated information, please report it to the
                research team.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReferencesSection;
