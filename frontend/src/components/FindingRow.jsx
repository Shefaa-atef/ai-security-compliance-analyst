import { useI18n } from "../i18n/useI18n";
import { requirements } from "../data/requirements";
import Icon from "./Icon";
export default function FindingRow({ finding }) {
  const { t } = useI18n();
  const requirement = requirements.find(
    (item) => item.id === finding.requirement_id,
  );
  return (
    <details className="finding">
      <summary>
        <span className={`finding-indicator ${finding.status}`}>
          {finding.status === "supported" ? (
            <Icon name="check" size={12} />
          ) : (
            "?"
          )}
        </span>
        <span className="finding-name">
          <span className="requirement-id">{requirement.id}</span>
          <strong>{t(`requirements.${requirement.id}.title`)}</strong>
        </span>
        <span className={`finding-status ${finding.status}`}>
          {t(`status.${finding.status}`)}
        </span>
        <Icon name="chevron" size={13} />
      </summary>
      <div className="finding-content">
        <p className="requirement-text">
          {t(`requirements.${requirement.id}.description`)}
        </p>
        <h4>{t("finding.evidence")} </h4>
        {finding.evidence.length ? (
          finding.evidence.map((quote, index) => (
            <blockquote key={index} dir="auto">
              {quote}
            </blockquote>
          ))
        ) : (
          <p>{t("finding.noEvidence")} </p>
        )}
        <h4>{t("finding.assessment")} </h4>
        <p dir="auto">{finding.explanation}</p>
        <h4>{t("finding.action")} </h4>
        <p dir="auto">{finding.recommendation}</p>
      </div>
    </details>
  );
}
