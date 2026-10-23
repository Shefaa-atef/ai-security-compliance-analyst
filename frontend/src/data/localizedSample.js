import { sampleAssessment } from "./sampleAssessment.js";
// Only authored sample content is localized. Live evidence stays as returned.
export function getLocalizedSample(t) {
  return {
    ...sampleAssessment,
    summary: t("sample.summary"),
    risk_rationale: t("sample.risk_rationale"),
    findings: sampleAssessment.findings.map((finding) => ({
      ...finding,
      evidence: finding.evidence.map((_, index) =>
        t(`sample.${finding.requirement_id}.evidence.${index}`),
      ),
      explanation: t(`sample.${finding.requirement_id}.explanation`),
      recommendation: t(`sample.${finding.requirement_id}.recommendation`),
    })),
    ...Object.fromEntries(
      ["next_actions", "follow_up_questions", "review_steps"].map((field) => [
        field,
        sampleAssessment[field].map((_, index) =>
          t(`sample.${field}.${index}`),
        ),
      ]),
    ),
  };
}
