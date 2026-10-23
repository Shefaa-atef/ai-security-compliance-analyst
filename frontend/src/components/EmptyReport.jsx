import Icon from "./Icon";
export default function EmptyReport({ loading }) {
  return (
    <div className="empty-report" role="status">
      <div className={`report-symbol ${loading ? "is-loading" : ""}`}>
        <div className="symbol-orbit" />
        <Icon name={loading ? "spark" : "shield"} size={42} />
      </div>
      <h3>
        {loading
          ? "A closer look, in progress."
          : "Your next step, made clearer."}
      </h3>
      <p>
        {loading
          ? "Reviewing the scenario against the governance framework. This may take a moment."
          : "Turn a scenario into an evidence-linked review of risks, controls, and next steps."}
      </p>
      <div className="preview-stack">
        <div>
          <Icon name="document" size={17} />
          <span>Eight governance requirements</span>
          <span className="mini-line" />
        </div>
        <div>
          <Icon name="chat" size={17} />
          <span>Evidence behind each finding</span>
          <span className="mini-line" />
        </div>
        <div>
          <Icon name="arrow" size={17} />
          <span>Clear, practical next actions</span>
          <span className="mini-line" />
        </div>
      </div>
      <span className="empty-caption">
        {loading
          ? "You can keep this page open while we review."
          : "Start with the sample, or bring your own scenario."}
      </span>
    </div>
  );
}
