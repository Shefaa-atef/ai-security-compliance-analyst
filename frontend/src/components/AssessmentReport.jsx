import Icon from "./Icon";
import FindingRow from "./FindingRow";
import EmptyReport from "./EmptyReport";
export default function AssessmentReport({ result, loading, reportRef }) {
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = result.isSample
      ? "sample-assessment.json"
      : "assessment.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <section
      className="panel report-panel"
      ref={reportRef}
      aria-labelledby="report-heading"
      aria-busy={loading}
    >
      <div className="panel-heading">
        <span className="step-label">
          02 <span>THE ASSESSMENT</span>
        </span>
        {result ? (
          <button className="export-button" onClick={download}>
            <Icon name="download" size={15} /> Export JSON
          </button>
        ) : (
          <span className="subtle-pill">Evidence first</span>
        )}
      </div>
      <div className="report-title">
        <h2 id="report-heading">A clearer perspective.</h2>
        {result && (
          <span className="subtle-pill">
            {result.isSample ? "Sample report" : "AI-generated"}
          </span>
        )}
      </div>
      {!result ? (
        <EmptyReport loading={loading} />
      ) : (
        <div className="report-body">
          {result.isSample && (
            <div className="sample-banner">
              Illustrative customer support assessment · Not an AI-generated
              result
            </div>
          )}
          <div className="risk-summary">
            <span className={`risk-pill risk-${result.risk_level}`}>
              <span /> {result.risk_level} risk
            </span>
            <h3>Review before moving forward.</h3>
            <p>{result.summary}</p>
            <details className="risk-detail">
              <summary>Why this risk level?</summary>
              <p>{result.risk_rationale}</p>
            </details>
          </div>
          <div className="findings-heading">
            <h3>Requirement review</h3>
            <span>Expand to see the evidence</span>
          </div>
          <div className="findings-list">
            {result.findings.map((finding) => (
              <FindingRow key={finding.requirement_id} finding={finding} />
            ))}
          </div>
          <section className="next-actions">
            <h3>What comes next</h3>
            <ol>
              {result.next_actions.map((action, index) => (
                <li key={index}>
                  <span>{index + 1}</span>
                  {action}
                </li>
              ))}
            </ol>
          </section>
          {result.follow_up_questions.length > 0 && (
            <details className="follow-up">
              <summary>
                Questions to take back to your team{" "}
                <Icon name="chevron" size={14} />
              </summary>
              <ul>
                {result.follow_up_questions.map((question, index) => (
                  <li key={index}>{question}</li>
                ))}
              </ul>
            </details>
          )}
          <details className="follow-up">
            <summary>
              Review activity <Icon name="chevron" size={14} />
            </summary>
            <ul>
              {result.review_steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
            <small>Reference: {result.assessment_id}</small>
          </details>
          <p className="report-disclaimer">
            <Icon name="shield" size={16} /> An initial assessment, not
            deployment approval. A governance reviewer must validate the
            findings.
          </p>
        </div>
      )}
    </section>
  );
}
