import "./ScenarioForm.css";
import { useI18n } from "../i18n/useI18n";
import { scenarios } from "../data/scenarios";
import Icon from "./Icon";
export default function ScenarioForm({
  mode,
  onModeChange,
  scenario,
  onScenarioChange,
  onSubmit,
  loading,
  error,
}) {
  const { t, formatNumber } = useI18n();
  const sample = mode === "sample";
  return (
    <section className="panel input-panel" aria-labelledby="scenario-heading">
      <div className="panel-heading">
        <span className="step-label">
          {formatNumber(1)} <span>{t("form.eyebrow")} </span>
        </span>
        <span className="subtle-pill">{t("form.start")} </span>
      </div>
      <h2 id="scenario-heading">{t("form.heading")} </h2>
      <p className="section-description">
        {t("form.description")} <br />
        {t("form.detail")}{" "}
      </p>
      <div className="segmented" aria-label={t("form.mode")}>
        <button
          aria-pressed={sample}
          onClick={() => onModeChange("sample")}
          disabled={loading}
        >
          {t("form.sampleTab")}{" "}
        </button>
        <button
          aria-pressed={!sample}
          onClick={() => onModeChange("api")}
          disabled={loading}
        >
          {t("form.apiTab")}{" "}
        </button>
      </div>
      <form onSubmit={onSubmit}>
        <fieldset disabled={loading}>
          <legend>
            {sample ? t("form.sampleLegend") : t("form.exampleLegend")}
          </legend>
          <div className="scenario-options">
            {scenarios.map((item, index) => (
              <button
                key={item.id}
                type="button"
                disabled={sample && index !== 0}
                className={`scenario-option ${(sample && index === 0) || (!sample && scenario === t(`scenarios.${item.id}.text`)) ? "selected" : ""}`}
                onClick={() => onScenarioChange(t(`scenarios.${item.id}.text`))}
              >
                <span className={`scenario-icon icon-${item.id}`}>
                  <Icon name={item.icon} />
                </span>
                <span>
                  <strong>{t(`scenarios.${item.id}.title`)}</strong>
                  <small>{t(`scenarios.${item.id}.subtitle`)}</small>
                </span>
                <Icon name="chevron" size={14} />
              </button>
            ))}
          </div>
          <label className="textarea-label" htmlFor="scenario">
            {sample ? t("form.sampleLabel") : t("form.inputLabel")}
            <span>{sample ? t("form.readonly") : t("form.length")}</span>
          </label>
          <textarea
            id="scenario"
            name="scenario"
            dir="auto"
            value={sample ? t("scenarios.support.text") : scenario}
            onChange={(event) => onScenarioChange(event.target.value)}
            readOnly={sample}
            required={!sample}
            minLength={sample ? undefined : 20}
            maxLength={12000}
            placeholder={t("form.placeholder")}
            aria-describedby="input-guidance"
          />
          <p id="input-guidance" className="input-guidance">
            <Icon name="lock" size={14} />
            {t("form.privacy")}{" "}
          </p>
        </fieldset>
        {sample && <p className="sample-note">{t("form.sampleNote")} </p>}
        {error && (
          <div className="error-message" role="alert">
            {t(error)}
          </div>
        )}
        <button
          className="primary-button"
          type="submit"
          disabled={loading || (!sample && scenario.trim().length < 20)}
        >
          {loading ? (
            <>
              <span className="spinner" />
              {t("form.loading")}{" "}
            </>
          ) : (
            <>
              {sample ? t("form.preview") : t("form.assess")}
              <Icon name="arrow" size={18} />
            </>
          )}
        </button>
        <p className="button-caption">
          {sample ? t("form.sampleCaption") : t("form.apiCaption")}
        </p>
        {!sample && (
          <p className="button-caption">{t("form.outputLanguage")}</p>
        )}
      </form>
    </section>
  );
}
