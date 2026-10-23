import { useRef, useState } from "react";
import Header from "./components/Header";
import ScenarioForm from "./components/ScenarioForm";
import AssessmentReport from "./components/AssessmentReport";
import RequirementsPanel from "./components/RequirementsPanel";
import { sampleAssessment } from "./data/sampleAssessment";
import { assessScenario } from "./lib/api";
import "./App.css";

export default function App() {
  const [mode, setMode] = useState("sample");
  const [scenario, setScenario] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showRequirements, setShowRequirements] = useState(false);
  const reportRef = useRef(null);
  function changeMode(value) {
    setMode(value);
    setResult(null);
    setError("");
  }
  function changeScenario(value) {
    setScenario(value);
    setResult(null);
    setError("");
  }
  async function submit(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      // Sample mode previews a fixed report; it never evaluates user input.
      const assessment =
        mode === "sample"
          ? sampleAssessment
          : await assessScenario(scenario.trim());
      setResult({ ...assessment, isSample: mode === "sample" });
      requestAnimationFrame(() =>
        reportRef.current?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)")
            .matches
            ? "auto"
            : "smooth",
          block: "start",
        }),
      );
    } catch (failure) {
      setError(failure.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <>
      <Header
        onRequirements={() => setShowRequirements(!showRequirements)}
        expanded={showRequirements}
      />
      <main>
        <section className="intro">
          <div className="eyebrow">
            <span className="status-dot" /> ACME FINANCIAL SERVICES
          </div>
          <h1>
            Clarity before
            <br />
            <span>you deploy.</span>
          </h1>
          <p>
            A thoughtful first look at your AI use case.
            <br className="desktop-break" /> Understand the risks. See the
            evidence. Know what comes next.
          </p>
          <div className="intro-caption">
            AI security & compliance analyst <span> / </span> Human judgment,
            supported.
          </div>
        </section>
        {showRequirements && <RequirementsPanel />}
        <div className="workspace">
          <ScenarioForm
            mode={mode}
            onModeChange={changeMode}
            scenario={scenario}
            onScenarioChange={changeScenario}
            onSubmit={submit}
            loading={loading}
            error={error}
          />
          <AssessmentReport
            result={result}
            loading={loading}
            reportRef={reportRef}
          />
        </div>
        <footer>
          <span>
            Acme <strong>·</strong> AI Governance
          </span>
          <span>Initial guidance. Always reviewed by a person.</span>
        </footer>
      </main>
    </>
  );
}
