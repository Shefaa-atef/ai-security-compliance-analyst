import { useI18n } from "../i18n/useI18n";
import Icon from "./Icon";

export default function GuardrailNotes({ notes }) {
  const { t } = useI18n();
  if (!notes?.length) return null;

  return (
    <section className="guardrail-notes" aria-labelledby="guardrail-heading">
      <h3 id="guardrail-heading">
        <Icon name="shield" size={16} />
        {t("report.guardrails")}
      </h3>
      <p>{t("report.guardrailsDescription")}</p>
      <ul>
        {notes.map((note, index) => (
          <li key={index} dir="auto">
            {note}
          </li>
        ))}
      </ul>
    </section>
  );
}
