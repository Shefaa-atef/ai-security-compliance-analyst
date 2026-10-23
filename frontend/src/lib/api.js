import { requirements, statusLabels } from "../data/requirements";
const riskLevels = ["low", "medium", "high", "unknown"];
const isText = (value) => typeof value === "string" && value.trim().length > 0;
const isTextList = (value) => Array.isArray(value) && value.every(isText);
// Reject malformed results rather than displaying partial or misleading findings.
export function validateAssessment(data) {
  if (
    !data ||
    !isText(data.assessment_id) ||
    !isText(data.summary) ||
    !riskLevels.includes(data.risk_level) ||
    !isText(data.risk_rationale) ||
    !isTextList(data.next_actions) ||
    !isTextList(data.follow_up_questions) ||
    !isTextList(data.review_steps) ||
    !Array.isArray(data.findings) ||
    data.findings.length !== 8
  )
    throw new Error(
      "The assessment service returned an unexpected report format. Please try again.",
    );
  const ids = new Set();
  for (const finding of data.findings) {
    if (
      !finding ||
      !requirements.some((item) => item.id === finding.requirement_id) ||
      ids.has(finding.requirement_id) ||
      !Object.hasOwn(statusLabels, finding.status) ||
      !isTextList(finding.evidence) ||
      !isText(finding.explanation) ||
      !isText(finding.recommendation)
    )
      throw new Error(
        "The assessment service returned invalid requirement findings. Please try again.",
      );
    ids.add(finding.requirement_id);
  }
  return data;
}
export async function assessScenario(scenario) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const baseUrl = (import.meta.env.VITE_API_BASE_URL || "").replace(
      /\/$/,
      "",
    );
    const response = await fetch(`${baseUrl}/api/assess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario }),
      signal: controller.signal,
    });
    if (!response.ok) {
      const messages = {
        422: "Check your scenario: use between 20 and 12,000 characters.",
        429: "Too many requests. Wait a moment and try again.",
        503: "The AI assessment service is unavailable. Please try again shortly.",
      };
      throw new Error(
        messages[response.status] ||
          "The assessment could not be completed. Please try again.",
      );
    }
    return validateAssessment(await response.json());
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error("The assessment took too long. Please try again.");
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach the assessment service. Check that the Python backend is running.",
      );
    if (error instanceof SyntaxError)
      throw new Error(
        "The service did not return a valid report. Check the backend configuration.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
