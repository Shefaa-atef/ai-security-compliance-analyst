import "./FindingOverview.css";
import { useI18n } from "../i18n/useI18n";

export default function FindingOverview({ findings }) {
  const { t, formatNumber } = useI18n();
  const statuses = [
    "supported",
    "gap",
    "needs_clarification",
    "not_applicable",
  ];

  return (
    <dl className="finding-overview" aria-label={t("report.counts")}>
      {statuses.map((status) => (
        <div key={status} className={`overview-item overview-${status}`}>
          <dd>
            {formatNumber(
              findings.filter((finding) => finding.status === status).length,
            )}
          </dd>
          <dt>{t(`status.${status}`)}</dt>
        </div>
      ))}
    </dl>
  );
}
