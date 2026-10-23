# Backend handoff: AI Security & Compliance Analyst

Current API extension: requests may include `response_language` (`en` or `ar`, default `en`); responses record it. Narrative and server messages follow that language, while evidence stays in the original scenario language.

Build only the Python backend in `backend/`. The React frontend is implemented separately. Do not edit frontend files or change this API contract without coordination. Use FastAPI and Pydantic, with small modules for routes, schemas, requirement catalog, agent workflow, and model integration. Use original implementation and standard libraries/SDKs; no pre-built assessment solution.

## Scope and priorities

1. Create the FastAPI application, dependency file, `.env.example` with placeholders, and setup instructions. Never commit credentials.
2. Add the eight internal requirements, using the exact IDs and wording in `frontend/src/data/requirements.js` as reference; keep an authoritative Python catalog.
3. Implement the validated API below.
4. Implement a purposeful agent workflow: extract scenario facts and information needs; call a requirement lookup tool against the catalog; assess evidence and gaps; produce structured recommendations; validate the final response. Record concise actual workflow activity, not private chain-of-thought. If tools are selected deterministically, explain that honestly in the README.
5. Connect a real LLM using a server-only API key and a configurable model. Use structured outputs supported by the chosen provider. No silent mock fallback. Missing credentials or provider failure must return a safe service error.
6. Test all three supplied scenarios, malformed/blank/oversized input, prompt injection attempts, malformed model outputs, timeouts, and provider failures. Include deterministic tests with a mocked provider, and clearly distinguish those from a live model check.

## API contract (frontend already uses this)

Development address: `http://127.0.0.1:8000`. Vite proxies `/api` to that address. Optional `VITE_API_BASE_URL` supports another origin; restrict backend CORS to configured frontend origins (local defaults `http://localhost:5173` and `http://127.0.0.1:5173`).

### POST /api/assess

Request JSON:

```json
{ "scenario": "A scenario between 20 and 12000 characters after trimming." }
```

Successful response: HTTP 200, application/json, no envelope. Return exactly one finding for each AI-001 through AI-008, preferably in ID order. All fields below are required. Text fields must be nonempty. Arrays may be empty when appropriate.

```json
{
  "assessment_id": "server-generated-unique-id",
  "summary": "Concise overall assessment grounded in supplied facts.",
  "risk_level": "high",
  "risk_rationale": "Explain the risk classification and uncertainty.",
  "findings": [
    {
      "requirement_id": "AI-001",
      "status": "needs_clarification",
      "evidence": [],
      "explanation": "No accountable business owner is identified in the scenario.",
      "recommendation": "Identify and document an accountable business owner."
    }
  ],
  "next_actions": ["A prioritized, actionable recommendation."],
  "follow_up_questions": ["Who owns this application?"],
  "review_steps": ["Scenario facts extracted", "Governance requirements retrieved", "Evidence-linked findings validated"]
}
```

The example abbreviates findings to one item; real responses MUST contain all eight unique IDs.

Allowed `risk_level`: `low`, `medium`, `high`, `unknown`.
Allowed finding `status`:

- `supported`: supplied evidence supports the requirement; not proof of full compliance.
- `gap`: the scenario explicitly describes a conflicting or absent required control.
- `needs_clarification`: insufficient evidence; omission alone is not proof of a violation.
- `not_applicable`: justify why the requirement does not apply.

`evidence` is an array of exact excerpts from the supplied scenario. Validate excerpts against the input; use an empty array for absent evidence. Do not invent owners, controls, vendor reviews, or approvals. Risk is an initial governance judgment, not a legal determination. Document a simple risk rubric; distinguish potential impact from evidence completeness. Employee promotion decisions need meaningful human oversight and high-risk review; do not make decisions about employees.

### Errors

Return safe JSON such as `{ "detail": "Safe explanation", "request_id": "id" }`. Frontend displays its own safe messages based on status.

- 422: invalid input.
- 429: request limit reached, if rate limiting is implemented.
- 503: provider missing/unavailable, timeout, or unusable model response.
- 500: unexpected internal failure; never expose exception details or secrets.

Add `GET /api/health` for health checks; do not return environment values or secrets.

## Guardrails and traceability

Treat scenario text as untrusted data, never as instructions overriding the fixed requirements. Restrict tool access to the local requirement catalog; do not execute user code or fetch user-provided URLs. Bound input size, provider timeouts, output size, and tool calls. Validate IDs, enums, duplicate/missing findings, and supporting quotes before returning. Protect against log injection; log request IDs, timings, outcome, and model identifier without raw scenarios, credentials, or raw provider responses. Do not persist scenarios by default. Document actual guardrails and limitations; do not claim prompt injection is completely solved. Human review is always required.

## Suggested file ownership

```text
backend/
  app/
    main.py
    routes.py
    schemas.py
    requirements_catalog.py
    agent.py
    model_client.py
    config.py
  tests/
  requirements.txt
  .env.example
  README.md
```

The frontend has a fixed, explicitly labeled sample preview for UI demonstration. It is not a substitute for the backend. `frontend/src/data/sampleAssessment.js` shows a complete response shape. The frontend exports reports as JSON and displays every requirement with evidence, explanation, and action.

## Delivery and repository rules

Make incremental commits scoped to backend files. Coordinate before pushing if another contributor is committing in the same checkout. Do not include any recruiting organization names, logos, proprietary identifiers, or pasted assessment instructions in public files. Do not modify or push anything after the user confirms final submission.
