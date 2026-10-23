import { useI18n } from "../i18n/useI18n";
import "./ReportLanguageNotice.css";

export default function ReportLanguageNotice({
  language,
  loading,
  onReassess,
}) {
  const { locale, t } = useI18n();
  const name = t(`language.names.${language}`);
  const differentLanguage = language !== locale;
  return (
    <div
      className={`report-language ${differentLanguage ? "report-language-mismatch" : ""}`}
    >
      <p>
        {t(differentLanguage ? "report.languageMismatch" : "report.language", {
          language: name,
        })}
      </p>
      {differentLanguage && onReassess && (
        <button type="button" disabled={loading} onClick={onReassess}>
          {t("report.reassessLanguage", {
            language: t(`language.names.${locale}`),
          })}
        </button>
      )}
    </div>
  );
}
