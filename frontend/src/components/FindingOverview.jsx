import { statusLabels } from "../data/requirements";

export default function FindingOverview({ findings }) {
  const statuses = [
    "supported",
    "gap",
    "needs_clarification",
    "not_applicable",
  ];

  return (
    <dl className="finding-overview" aria-label="Requirement finding totals">
      {statuses.map((status) => (
        <div key={status} className={`overview-item overview-${status}`}>
          <dd>
            {findings.filter((finding) => finding.status === status).length}
          </dd>
          <dt>{statusLabels[status]}</dt>
        </div>
      ))}
    </dl>
  );
}
