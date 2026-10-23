import { useI18n } from "./i18n/useI18n";
import { useRef, useState } from "react";
import Header from "./components/Header";
import ScenarioForm from "./components/ScenarioForm";
import AssessmentReport from "./components/AssessmentReport";
import RequirementsPanel from "./components/RequirementsPanel";
import { sampleAssessment } from "./data/sampleAssessment";
import { getLocalizedSample } from "./data/localizedSample";
import { assessScenario } from "./lib/api";
import "./App.css";

export default function App() {
  const { t } = useI18n();
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
      setError(
        failure.message.startsWith("errors.")
          ? failure.message
          : "errors.failed",
      );
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
            <span className="status-dot" />
            {t("intro.organization")}{" "}
          </div>
          <h1>
            {t("intro.heading")} <br />
            <span>{t("intro.highlight")} </span>
          </h1>
          <p>
            {t("intro.description")} <br className="desktop-break" />
            {t("intro.detail")}{" "}
          </p>
          <div className="intro-caption">
            {t("intro.caption")} <span> / </span>
            {t("intro.human")}{" "}
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
            result={
              result?.isSample
                ? { ...getLocalizedSample(t), isSample: true }
                : result
            }
            loading={loading}
            reportRef={reportRef}
          />
        </div>
        <footer>
          <span>
            {t("brand.name")} <strong>·</strong>
            {t("brand.governance")}{" "}
          </span>
          <span>{t("footer.guidance")} </span>
        </footer>
      </main>
    </>
  );
}
