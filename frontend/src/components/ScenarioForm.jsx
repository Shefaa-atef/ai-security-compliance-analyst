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
  const sample = mode === "sample";
  return (
    <section className="panel input-panel" aria-labelledby="scenario-heading">
      <div className="panel-heading">
        <span className="step-label">
          01 <span>THE USE CASE</span>
        </span>
        <span className="subtle-pill">Start here</span>
      </div>
      <h2 id="scenario-heading">What are you building?</h2>
      <p className="section-description">
        Give your AI use case a little context.
        <br />
        We’ll help you see the bigger picture.
      </p>
      <div className="segmented" aria-label="Assessment mode">
        <button
          aria-pressed={sample}
          onClick={() => onModeChange("sample")}
          disabled={loading}
        >
          Sample preview
        </button>
        <button
          aria-pressed={!sample}
          onClick={() => onModeChange("api")}
          disabled={loading}
        >
          Assess a scenario
        </button>
      </div>
      <form onSubmit={onSubmit}>
        <fieldset disabled={loading}>
          <legend>
            {sample
              ? "Preview a customer support assessment"
              : "Start with an example"}
          </legend>
          <div className="scenario-options">
            {scenarios.map((item, index) => (
              <button
                key={item.id}
                type="button"
                disabled={sample && index !== 0}
                className={`scenario-option ${(sample && index === 0) || (!sample && scenario === item.text) ? "selected" : ""}`}
                onClick={() => onScenarioChange(item.text)}
              >
                <span className={`scenario-icon icon-${item.id}`}>
                  <Icon name={item.icon} />
                </span>
                <span>
                  <strong>{item.title}</strong>
                  <small>{item.subtitle}</small>
                </span>
                <Icon name="chevron" size={14} />
              </button>
            ))}
          </div>
          <label className="textarea-label" htmlFor="scenario">
            {sample ? "Sample scenario" : "Describe your scenario"}
            <span>{sample ? "Read only" : "20–12,000 characters"}</span>
          </label>
          <textarea
            id="scenario"
            value={sample ? scenarios[0].text : scenario}
            onChange={(event) => onScenarioChange(event.target.value)}
            readOnly={sample}
            required={!sample}
            minLength={sample ? undefined : 20}
            maxLength={12000}
            placeholder="What will the AI do? Who will use it? Describe the information it handles, its controls, and how people will review its outputs."
            aria-describedby="input-guidance"
          />
          <p id="input-guidance" className="input-guidance">
            <Icon name="lock" size={14} /> Use fictional or sanitized
            information. Leave out secrets and personal data.
          </p>
        </fieldset>
        {sample && (
          <p className="sample-note">
            A fixed, illustrative report. No AI call is made in sample preview.
          </p>
        )}
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}
        <button
          className="primary-button"
          type="submit"
          disabled={loading || (!sample && scenario.trim().length < 20)}
        >
          {loading ? (
            <>
              <span className="spinner" /> Reviewing your scenario…
            </>
          ) : (
            <>
              {sample ? "Explore sample assessment" : "Assess scenario"}
              <Icon name="arrow" size={18} />
            </>
          )}
        </button>
        <p className="button-caption">
          {sample
            ? "Explore the experience before connecting your backend."
            : "Your scenario is sent to the configured assessment service."}
        </p>
      </form>
    </section>
  );
}
