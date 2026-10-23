# Backend

Python API that assesses an AI use case against Acme Financial Services' eight AI governance requirements (AI-001 to AI-008). It uses a tool-using Claude agent wrapped in deterministic guardrails.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env          # then set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`, so no frontend configuration is needed locally.

## Testing

Deterministic tests use a scripted fake model client. They need no API key and cover the three supplied use cases, prompt injection, malformed and oversized input, malformed model output, timeouts, refusals, rate limiting and the response contract:

```bash
python -m pytest -q
```

The live check is separate. It sends the three supplied use cases to the real Claude API, so it needs a valid key and costs a small amount. Its results depend on the model:

```bash
python -m scripts.live_check
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness check and whether an AI key is configured |
| POST | `/api/assess` | Body `{"scenario": "..."}` (20 to 12,000 characters); returns the assessment report |

Error responses: `422` invalid scenario, `429` rate limit exceeded, `503` AI service unavailable, not configured, timed out or returned an unusable answer, `500` unexpected error. Error bodies look like `{"detail": "...", "request_id": "..."}`. They never echo the input or include provider messages or stack traces. Every response carries an `X-Request-ID` header that matches the audit log.

## How an assessment works

```text
scenario
  -> input guardrails     normalize, redact secrets and personal data, flag prompt injection
  -> Claude agent         decides which tools to call, then returns schema-valid JSON
       list_requirements          the governance catalog
       get_requirement_guidance   what satisfies each control and what signals a gap
       scan_risk_signals          deterministic scan of data types, third parties, automation, impact
  -> output guardrails    verify evidence, enforce policy rules and minimum risk level
  -> audit log            one JSON line per request, scenario stored only as a SHA-256 hash
  -> response             findings, risk, actions, review steps, guardrail notes
```

Tool selection is model-driven: the system prompt asks Claude to use the tools, and Claude decides which to call and with which requirement ids. The backend does not depend on that choice for safety. The output guardrails run the risk scan and the requirement checks themselves on every request. The review steps in the response list the tool calls that actually happened.

### Risk rubric

Risk describes potential impact, not how complete the description is. Missing information goes into findings and follow-up questions.

| Level | Meaning |
| --- | --- |
| high | Affects employment, finances, legal rights or access to services, or makes automated decisions with personal or financial data |
| medium | Processes sensitive, personal, confidential or security data, with a person making the decision |
| low | No sensitive data and no material effect on people or business decisions |
| unknown | Too vague to judge impact |

The model proposes the level. The deterministic floor described under Guardrails can only raise it.

| File | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI app, CORS, rate limiting, error mapping |
| `app/service.py` | Runs the pipeline and builds the review trail |
| `app/agent.py` | Claude tool-use loop and system prompt |
| `app/requirements_catalog.py` | Requirements and assessment guidance (the agent's knowledge base) |
| `app/risk_signals.py` | Deterministic risk-signal scan and risk floors |
| `app/input_guardrails.py` | Redaction and prompt-injection detection |
| `app/output_guardrails.py` | Evidence verification and policy enforcement |
| `app/audit.py` | Append-only JSON Lines audit log |
| `app/schemas.py` | Request, model-output and response schemas |

## Guardrails

Input:

- Control and zero-width characters are removed so hidden text cannot carry instructions.
- API keys, credentials, private keys, emails, phone numbers, card numbers (Luhn-checked), IBANs and national ID numbers are replaced with `[REDACTED_...]` before the model sees them. The assessor follows AI-002 itself.
- Prompt-injection phrases are flagged. The scenario is always passed inside `<scenario>` tags as untrusted data, and the system prompt tells the model never to follow instructions found there.

Agent:

- Structured outputs constrain the final answer to the assessment schema. Tools use strict schemas.
- The risk scan runs on the scenario held by the backend, so the model cannot feed it different text.
- The loop stops after a fixed number of turns and a 55-second overall time budget, just under the frontend's 60-second limit. Tool errors go back to the model instead of crashing the request.
- The prompt limits the assessor to the governance of the system. It must never evaluate or rank individual employees or customers.
- Requests opt in to Claude's server-side refusal fallback, so a safety-classifier decline is retried on another model before the request fails.

Output:

- Every evidence quote must appear verbatim in the scenario. Invented quotes are removed.
- A requirement cannot be `supported` without verified evidence.
- Automated decisions with no described human review are always an AI-003 gap.
- A third-party service makes AI-006 applicable.
- Risk cannot fall below the policy floor. Employment decisions are high risk. Automated decisions on personal or financial data are high risk. Sensitive data is at least medium risk.
- Every correction appears in `guardrail_notes`, and the review steps say a human governance reviewer must confirm the result.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | none | Required for assessments. Keep it in `backend/.env` only |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | Claude model used by the agent |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | CORS allow-list |
| `RATE_LIMIT_PER_MINUTE` | `10` | Per client address, in memory |
| `AUDIT_LOG_PATH` | `logs/audit.jsonl` | Ignored by Git |

## Known limitations

- Rate limiting and the audit log are single-process. A multi-instance deployment would need a shared store.
- Redaction and risk signals are pattern-based. They reduce risk but do not replace data classification.
- Prompt-injection detection is a heuristic. It is not a complete defense. The real protection is that the model's output cannot bypass the output guardrails.
- There is no user authentication. In a real deployment the API would sit behind company SSO.
- Results are preliminary and are meant to support a human governance reviewer, not replace one.
