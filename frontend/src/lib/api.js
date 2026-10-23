import { validateAssessment } from "./assessmentSchema.js";

export function createAssessmentClient({
  baseUrl = "",
  fetchImpl = globalThis.fetch,
  timeoutMs = 60000,
} = {}) {
  return async function assessScenario(scenario) {
    const trimmed = scenario.trim();
    if (trimmed.length < 20 || trimmed.length > 12000)
      throw new Error("errors.validation");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetchImpl(
        `${baseUrl.replace(/\/$/, "")}/api/assess`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario: trimmed }),
          signal: controller.signal,
        },
      );
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
  };
}

export const assessScenario = createAssessmentClient({
  baseUrl: import.meta.env?.VITE_API_BASE_URL || "",
});
