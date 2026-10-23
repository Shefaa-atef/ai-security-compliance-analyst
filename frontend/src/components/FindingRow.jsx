import { requirements, statusLabels } from "../data/requirements";
import Icon from "./Icon";
export default function FindingRow({ finding }) {
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
          <strong>{requirement.title}</strong>
        </span>
        <span className={`finding-status ${finding.status}`}>
          {statusLabels[finding.status]}
        </span>
        <Icon name="chevron" size={13} />
      </summary>
      <div className="finding-content">
        <p className="requirement-text">{requirement.description}</p>
        <h4>Scenario evidence</h4>
        {finding.evidence.length ? (
          finding.evidence.map((quote, index) => (
            <blockquote key={index}>{quote}</blockquote>
          ))
        ) : (
          <p>No supporting evidence provided in the scenario.</p>
        )}
        <h4>Assessment</h4>
        <p>{finding.explanation}</p>
        <h4>Recommended action</h4>
        <p>{finding.recommendation}</p>
      </div>
    </details>
  );
}
