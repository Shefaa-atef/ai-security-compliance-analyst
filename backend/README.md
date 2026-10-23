# Backend

FastAPI service that assesses a proposed AI use case against Acme Financial Services' eight governance requirements (AI-001 to AI-008).

A Gemini or Claude agent drafts the assessment using local tools. Deterministic guardrails then check the draft before anything reaches the user.

## Quick start

Requires Python 3.11 or later and a Gemini API key (or an Anthropic key for the optional Claude adapter).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # Windows: copy .env.example .env
# Set AI_PROVIDER=gemini and GEMINI_API_KEY in .env
uvicorn app.main:app --reload --port 8000
```

The frontend dev server proxies `/api` to port 8000, so no extra configuration is needed locally.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness, and whether an AI key is configured |
| `POST` | `/api/assess` | Assess one scenario of 20 to 12,000 characters |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/assess \
  -H "Content-Type: application/json" \
  -d '{"scenario": "HR wants to use an AI system to automatically recommend employees for promotion."}'
```

Example response, abbreviated and illustrative:

```json
{
  "assessment_id": "0b6f6c1e-…",
  "summary": "Automated promotion recommendations without human review conflict with oversight requirements.",
  "risk_level": "high",
  "risk_rationale": "Decisions about employees are high impact. A governance reviewer must confirm this rating.",
  "findings": [
    {
      "requirement_id": "AI-003",
      "status": "gap",
      "evidence": ["automatically recommend employees for promotion"],
      "explanation": "Recommendations drive promotion decisions and no human review is described.",
      "recommendation": "Require a qualified person to review and approve every recommendation."
    }
  ],
  "next_actions": ["Define human review of every recommendation before use."],
  "follow_up_questions": ["Who is accountable for promotion decisions?"],
  "review_steps": [
    "Input guardrails applied: 0 sensitive value(s) redacted; no prompt-injection patterns found.",
    "Agent retrieved the governance requirement catalog.",
    "Agent ran the risk-signal scan.",
    "Output guardrails: 4 evidence quote(s) verified against the scenario, 0 removed, 1 status change(s)."
  ],
  "guardrail_notes": ["AI-003 changed to gap: the AI output drives decisions and no human review is described."],
  "model": "gemini-3.5-flash-lite"
}
```

A real response always contains all eight findings.

Errors return `{"detail": "...", "request_id": "..."}` and never echo the scenario or provider messages.

| Status | Meaning |
| --- | --- |
| `422` | Scenario missing, too short or too long after trimming |
| `429` | Rate limit reached |
| `503` | AI not configured, unavailable, timed out or returned an unusable answer |
| `500` | Unexpected error |

## How an assessment works

```text
scenario
  1. input guardrails    strip invisible characters, redact secrets and personal data, flag injection
  2. AI agent            calls local tools, then returns JSON that must match the schema
                           list_requirements          requirement catalog
                           get_requirement_guidance   what satisfies each control, what signals a gap
                           scan_risk_signals          data types, third parties, automation, impact
  3. output guardrails   verify evidence quotes, apply policy rules and the minimum risk level
  4. audit log           one JSON line per request, scenario stored only as a SHA-256 hash
  5. response            findings, risk, actions, review steps and guardrail notes
```

The selected model decides which local tools to call. The Gemini adapter requires successful catalog, guidance, and risk-scan tool calls before accepting the final assessment. Safety does not depend on that choice, because step 3 runs the risk scan and every rule itself. The review steps come from the backend and list the tool calls that actually happened.

### Guardrails

| Stage | Control |
| --- | --- |
| Input | Removes control and format characters that can hide text |
| Input | Redacts API keys, credentials, private keys, emails, phone numbers, card numbers, IBANs and national IDs |
| Input | Flags prompt-injection phrases. The scenario is always sent inside `<scenario>` tags as data |
| Agent | Structured outputs and strict tool schemas. Read-only local tools only |
| Agent | Turn limit and a 55-second time budget, under the frontend's 60-second limit |
| Agent | Anthropic-only refusal fallback is explicitly requested; Gemini has no provider fallback |
| Output | Evidence quotes must appear verbatim in the scenario, otherwise they are removed |
| Output | A requirement cannot be `supported` without verified evidence |
| Output | Automated decisions without described human review are always an AI-003 gap |
| Output | A detected third party makes AI-006 applicable. High risk requires evidence for AI-008 |
| Output | Risk cannot fall below the policy floor |

Every output correction appears in `guardrail_notes`.

### Risk rubric

Risk reflects potential impact, not how complete the description is. The model proposes a level and the policy floor can only raise it.

| Level | Meaning | Policy floor applies when |
| --- | --- | --- |
| high | Affects employment, finances, rights or access to services | Employment decisions, or automated decisions on personal or financial data |
| medium | Sensitive, personal, confidential or security data, with a person deciding | Sensitive data is processed |
| low | No sensitive data and no material effect on people | |
| unknown | Too vague to judge impact | |

## Code layout

```text
app/
  main.py              app factory, CORS and request ids
  config.py            settings from environment variables or .env
  schemas.py           request, model-output and response models
  pipeline.py          runs one assessment from input to audit entry
  review_trail.py      builds the review steps from what actually ran
  audit.py             append-only JSON Lines audit log
  rate_limit.py        in-memory sliding-window limiter
  api/                 routes, dependencies, safe error handlers
  agent/               system prompt, tool definitions, tool-use loop
  governance/          requirement catalog, risk-signal scan, example use cases
  guardrails/          input checks, evidence checks, policy rules
tests/                 deterministic tests with a scripted model
scripts/live_check.py  runs the three use cases against the real API
```

## Testing

```bash
python -m pytest -q        # deterministic, no API key needed
ruff check . && ruff format --check .
python -m scripts.live_check   # live: needs a valid key, costs a small amount
```

The deterministic tests script the model's replies. They cover the agent loop, all three supplied use cases, prompt injection, input validation, malformed model output, refusals, timeouts, rate limiting and the response contract. They prove the guardrails and plumbing, not the quality of the model's judgment. The live check covers that.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `AI_PROVIDER` | `anthropic` in code; `gemini` in the example | Selects `gemini` or `anthropic` |
| `GEMINI_API_KEY` | none | Required when using Gemini; backend only |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Tested alias; actual returned model is recorded |
| `ANTHROPIC_API_KEY` | none | Required only for the Anthropic adapter |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | Claude model used by the agent |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | CORS allow-list |
| `RATE_LIMIT_PER_MINUTE` | `10` | Per client address |
| `AUDIT_LOG_PATH` | `logs/audit.jsonl` | Ignored by Git |

## Limitations

- Redaction, injection detection and risk signals are pattern-based. They reduce risk but are not complete defenses.
- Rate limiting and the audit log are single-process. Several instances would need a shared store.
- There is no user authentication. A real deployment would sit behind company SSO.
- Reports are in English, even when the interface is in Arabic.
- Results are preliminary and support a human governance reviewer. They are not deployment approval.


### Evidence and risk review notes

Evidence matching tolerates differences in case, whitespace, and quote style, but returned excerpts are copied from the actual sanitized scenario text. This verifies that a quote exists; it does not prove that the quote semantically satisfies a control. A governance reviewer must confirm relevance.

A changed finding status also replaces the original explanation and recommendation so contradictory model conclusions are not retained. Vague scenarios can remain `unknown` risk. Automatic summarization alone is not classified as an automated business decision. Explicitly negated human review is not counted as an oversight control. High-risk review cannot be marked inapplicable merely because an unrelated quote is present.

The deterministic risk and injection patterns are primarily English. Arabic UI localization does not imply equivalent Arabic heuristic coverage. Use the supplied English examples for the assessed workflow and review other-language results carefully.


### Gemini implementation

The Google GenAI SDK executes a bounded, manually controlled function-calling loop. Automatic SDK tool execution is disabled. Tools are local and read-only; the model cannot replace the scenario passed to the risk scan. A final `submit_assessment` function with a Pydantic-derived JSON schema is made available only after all three context tools have succeeded. The resulting arguments are validated again before the shared output guardrails run. SDK retries are disabled so the adapter can enforce the request budget. The Gemini adapter has no provider or mock fallback.

Implementation references: [Google function calling](https://ai.google.dev/gemini-api/docs/generate-content/function-calling) and [Google structured output schemas](https://ai.google.dev/gemini-api/docs/structured-output). The model alias is configurable; live reports record the resolved model version when supplied by the API.

### Observed live verification

On 2026-10-23, all three fictional use cases completed with the Gemini adapter and returned eight findings, verified evidence, recommended actions, and an actual tool-use trail. The observed model was `gemini-3.5-flash-lite`: A and B were medium risk with human oversight supported; C was high risk with an oversight gap. Results are model-dependent, not golden expected outputs. No real customer or employee information was used.
