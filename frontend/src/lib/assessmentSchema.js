import { requirements, statusLabels } from "../data/requirements.js";
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
    (data.guardrail_notes !== undefined && !isTextList(data.guardrail_notes)) ||
    (data.model !== undefined && !isText(data.model)) ||
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
