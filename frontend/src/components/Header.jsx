import "./Header.css";
import LanguageSwitcher from "./LanguageSwitcher";
import { useI18n } from "../i18n/useI18n";
import Icon from "./Icon";
export default function Header({ onRequirements, expanded }) {
  const { t, formatNumber } = useI18n();
  return (
    <header className="topbar">
      <div className="nav-inner">
        <a className="brand" href="#" aria-label={t("brand.home")}>
          <span className="brand-mark">
            <Icon name="shield" size={22} />
          </span>
          <span>
            {t("brand.name")} <span className="brand-divider">/</span>
            <strong>{t("brand.governance")} </strong>
          </span>
        </a>
        <div className="header-actions">
          <LanguageSwitcher />
          <button
            className="nav-link"
            onClick={onRequirements}
            aria-expanded={expanded}
            aria-controls={expanded ? "requirements" : undefined}
          >
            {t("framework.label")}{" "}
            <span className="count-label">{formatNumber(8)}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
