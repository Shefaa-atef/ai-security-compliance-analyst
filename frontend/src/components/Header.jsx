import Icon from "./Icon";
export default function Header({ onRequirements, expanded }) {
  return (
    <header className="topbar">
      <div className="nav-inner">
        <a className="brand" href="#" aria-label="Acme AI governance home">
          <span className="brand-mark">
            <Icon name="shield" size={22} />
          </span>
          <span>
            Acme<span className="brand-divider">/</span>
            <strong>AI Governance</strong>
          </span>
        </a>
        <button
          className="nav-link"
          onClick={onRequirements}
          aria-expanded={expanded}
          aria-controls={expanded ? "requirements" : undefined}
        >
          Governance framework <span className="count-label">08</span>
        </button>
      </div>
    </header>
  );
}
