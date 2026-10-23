import "./RequirementsPanel.css";
import { useI18n } from "../i18n/useI18n";
import { requirements } from "../data/requirements";
export default function RequirementsPanel() {
  const { t } = useI18n();
  return (
    <section
      className="framework-panel"
      id="requirements"
      aria-label={t("framework.label")}
    >
      <div className="section-heading">
        <div>
          <span className="eyebrow">{t("framework.eyebrow")} </span>
          <h2>{t("framework.heading")} </h2>
        </div>
      </div>
      <div className="framework-grid">
        {requirements.map((item) => (
          <article key={item.id}>
            <span className="requirement-id">{item.id}</span>
            <h3>{t(`requirements.${item.id}.title`)}</h3>
            <p>{t(`requirements.${item.id}.description`)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
