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
    throw new Error("errors.format");
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
      throw new Error("errors.findings");
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
        422: "errors.validation",
        429: "errors.rateLimit",
        503: "errors.unavailable",
      };
      throw new Error(messages[response.status] || "errors.failed");
    }
    return validateAssessment(await response.json());
  } catch (error) {
    if (error.name === "AbortError") throw new Error("errors.timeout");
    if (error instanceof TypeError) throw new Error("errors.network");
    if (error instanceof SyntaxError) throw new Error("errors.json");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
