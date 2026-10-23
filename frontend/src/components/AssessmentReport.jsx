import { useI18n } from "../i18n/useI18n";
import Icon from "./Icon";
import FindingRow from "./FindingRow";
import EmptyReport from "./EmptyReport";
import FindingOverview from "./FindingOverview";
export default function AssessmentReport({ result, loading, reportRef }) {
  const { t, formatNumber } = useI18n();
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
          {formatNumber(2)} <span>{t("report.eyebrow")} </span>
        </span>
        {result ? (
          <button className="export-button" onClick={download}>
            <Icon name="download" size={15} />
            {t("report.export")}{" "}
          </button>
        ) : (
          <span className="subtle-pill">{t("report.evidenceFirst")} </span>
        )}
      </div>
      <div className="report-title">
        <h2 id="report-heading">{t("report.heading")} </h2>
        {result && (
          <span className="subtle-pill">
            {result.isSample ? t("report.sample") : t("report.generated")}
          </span>
        )}
      </div>
      {!result ? (
        <EmptyReport loading={loading} />
      ) : (
        <div className="report-body">
          {result.isSample && (
            <div className="sample-banner">{t("report.banner")} </div>
          )}
          <div className="risk-summary">
            <span className={`risk-pill risk-${result.risk_level}`}>
              <span /> {t(`risk.${result.risk_level}`)}
            </span>
            <h3>
              {result.risk_level === "high"
                ? t("report.highHeading")
                : result.risk_level === "unknown"
                  ? t("report.unknownHeading")
                  : t("report.defaultHeading")}
            </h3>
            <p dir="auto">{result.summary}</p>
            <details className="risk-detail">
              <summary>{t("report.whyRisk")} </summary>
              <p dir="auto">{result.risk_rationale}</p>
            </details>
          </div>
          <FindingOverview findings={result.findings} />
          <div className="findings-heading">
            <h3>{t("report.review")} </h3>
            <span>{t("report.expand")} </span>
          </div>
          <div className="findings-list">
            {result.findings.map((finding) => (
              <FindingRow key={finding.requirement_id} finding={finding} />
            ))}
          </div>
          <section className="next-actions">
            <h3>{t("report.actions")} </h3>
            <ol>
              {result.next_actions.map((action, index) => (
                <li key={index} dir="auto">
                  <span>{formatNumber(index + 1)}</span>
                  {action}
                </li>
              ))}
            </ol>
          </section>
          {result.follow_up_questions.length > 0 && (
            <details className="follow-up">
              <summary>
                {t("report.questions")} <Icon name="chevron" size={14} />
              </summary>
              <ul>
                {result.follow_up_questions.map((question, index) => (
                  <li key={index} dir="auto">
                    {question}
                  </li>
                ))}
              </ul>
            </details>
          )}
          <details className="follow-up">
            <summary>
              {t("report.activity")} <Icon name="chevron" size={14} />
            </summary>
            <ul>
              {result.review_steps.map((step, index) => (
                <li key={index} dir="auto">
                  {step}
                </li>
              ))}
            </ul>
            <small>
              {t("report.reference")} <bdi>{result.assessment_id}</bdi>
            </small>
          </details>
          <p className="report-disclaimer">
            <Icon name="shield" size={16} />
            {t("report.disclaimer")}{" "}
          </p>
        </div>
      )}
    </section>
  );
}
