import { useI18n } from "../i18n/useI18n";
import "./PageIntro.css";

export default function PageIntro() {
  const { t } = useI18n();
  return (
    <section className="intro" aria-labelledby="page-title">
      <div className="intro-copy">
        <div className="eyebrow">
          <span className="status-dot" />
          {t("intro.organization")}
        </div>
        <h1 id="page-title">
          {t("intro.heading")} <span>{t("intro.highlight")}</span>
        </h1>
        <p>
          {t("intro.description")} {t("intro.detail")}
        </p>
      </div>
      <div className="intro-caption">
        <span>{t("intro.caption")}</span>
        <strong>{t("intro.human")}</strong>
      </div>
    </section>
  );
}
