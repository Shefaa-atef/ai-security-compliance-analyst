import { useI18n } from "../i18n/useI18n";
import { locales } from "../i18n/config";
export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();
  return (
    <label className="language-switcher">
      <span className="sr-only">{t("language.label")}</span>
      <select
        value={locale}
        onChange={(event) => setLocale(event.target.value)}
        aria-label={t("language.label")}
      >
        {Object.entries(locales).map(([code, language]) => (
          <option key={code} value={code} lang={code}>
            {language.label}
          </option>
        ))}
      </select>
    </label>
  );
}
