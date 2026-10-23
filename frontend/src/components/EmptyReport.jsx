import "./EmptyReport.css";
import { useI18n } from "../i18n/useI18n";
import Icon from "./Icon";
export default function EmptyReport({ loading }) {
  const { t } = useI18n();
  return (
    <div className="empty-report" role="status">
      <div className={`report-symbol ${loading ? "is-loading" : ""}`}>
        <div className="symbol-orbit" />
        <Icon name={loading ? "spark" : "shield"} size={42} />
      </div>
      <h3>{loading ? t("empty.loadingHeading") : t("empty.heading")}</h3>
      <p>{loading ? t("empty.loadingDescription") : t("empty.description")}</p>
      <div className="preview-stack">
        <div>
          <Icon name="document" size={17} />
          <span>{t("empty.requirements")} </span>
          <span className="mini-line" />
        </div>
        <div>
          <Icon name="chat" size={17} />
          <span>{t("empty.evidence")} </span>
          <span className="mini-line" />
        </div>
        <div>
          <Icon name="arrow" size={17} />
          <span>{t("empty.actions")} </span>
          <span className="mini-line" />
        </div>
      </div>
      <span className="empty-caption">
        {loading ? t("empty.loadingCaption") : t("empty.caption")}
      </span>
    </div>
  );
}
