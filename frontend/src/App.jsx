import PageIntro from "./components/PageIntro";
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
  const { t, locale } = useI18n();
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
          : await assessScenario(scenario.trim(), locale);
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
        <PageIntro />
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
                ? {
                    ...getLocalizedSample(t),
                    isSample: true,
                    response_language: locale,
                  }
                : result
            }
            loading={loading}
            onReassess={submit}
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
