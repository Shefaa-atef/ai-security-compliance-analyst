import assert from "node:assert/strict";
import { test } from "node:test";
import { createAssessmentClient } from "../src/lib/api.js";
import { validateAssessment } from "../src/lib/assessmentSchema.js";
import { sampleAssessment } from "../src/data/sampleAssessment.js";

const scenario = "A fictional internal assistant with human review.";
const okResponse = (data) => ({ ok: true, json: async () => data });

test("accepts complete reports and validates optional backend traceability fields", () => {
  const report = {
    ...sampleAssessment,
    model: "test-model",
    guardrail_notes: ["One quote removed."],
  };
  assert.equal(validateAssessment(report), report);
  for (const mutate of [
    (d) => d.findings.pop(),
    (d) => (d.findings[0].requirement_id = "AI-999"),
    (d) => (d.findings[1].requirement_id = "AI-001"),
    (d) => (d.findings[0].status = "compliant"),
    (d) => (d.findings[0].evidence = "unsupported shape"),
    (d) => (d.guardrail_notes = [null]),
    (d) => (d.model = ""),
  ]) {
    const invalid = structuredClone(report);
    mutate(invalid);
    assert.throws(
      () => validateAssessment(invalid),
      /errors\.(format|findings)/,
    );
  }
});

test("sends the agreed request contract with trimmed input", async () => {
  let request;
  const assess = createAssessmentClient({
    baseUrl: "http://localhost:8000/",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return okResponse(sampleAssessment);
    },
  });
  await assess(`  ${scenario}  `);
  assert.equal(request.url, "http://localhost:8000/api/assess");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(request.options.body), { scenario });
});

test("rejects invalid input before making a request", async () => {
  const assess = createAssessmentClient({
    fetchImpl: () => assert.fail("Network must not be called"),
  });
  for (const input of [" ".repeat(30), "short", "a".repeat(12001)])
    await assert.rejects(() => assess(input), /errors.validation/);
});

test("maps HTTP errors to localized keys without leaking server details", async () => {
  for (const [status, key] of [
    [422, "validation"],
    [429, "rateLimit"],
    [503, "unavailable"],
    [500, "failed"],
  ]) {
    const assess = createAssessmentClient({
      fetchImpl: async () => ({
        ok: false,
        status,
        json: () => assert.fail("Never display provider error bodies"),
      }),
    });
    await assert.rejects(() => assess(scenario), new RegExp(`errors.${key}`));
  }
});

test("reports network, invalid JSON, malformed reports, and request timeout", async () => {
  const failing = (error) =>
    createAssessmentClient({
      fetchImpl: async () => {
        throw error;
      },
    });
  await assert.rejects(
    () => failing(new TypeError("connection refused"))(scenario),
    /errors.network/,
  );
  await assert.rejects(
    () => failing(new SyntaxError("not json"))(scenario),
    /errors.json/,
  );
  await assert.rejects(
    () =>
      createAssessmentClient({ fetchImpl: async () => okResponse({}) })(
        scenario,
      ),
    /errors.format/,
  );
  const assess = createAssessmentClient({
    timeoutMs: 5,
    fetchImpl: (_url, { signal }) =>
      new Promise((_, reject) => {
        signal.addEventListener(
          "abort",
          () => reject(new DOMException("Aborted", "AbortError")),
          { once: true },
        );
      }),
  });
  await assert.rejects(() => assess(scenario), /errors.timeout/);
});
