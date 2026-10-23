import { requirements } from "../data/requirements";
export default function RequirementsPanel() {
  return (
    <section
      className="framework-panel"
      id="requirements"
      aria-label="Governance framework"
    >
      <div className="section-heading">
        <div>
          <span className="eyebrow">THE FRAMEWORK</span>
          <h2>Eight requirements. One consistent review.</h2>
        </div>
      </div>
      <div className="framework-grid">
        {requirements.map((item) => (
          <article key={item.id}>
            <span className="requirement-id">{item.id}</span>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
