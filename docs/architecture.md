# Architecture and request walkthrough

This is a local AI governance assessment prototype. React collects a proposed AI use case; FastAPI coordinates model-driven policy lookup, structured analysis, deterministic checks, and a traceable report. It assesses systems against eight internal requirements; it does not make decisions about individual employees or approve deployment.

## Follow one assessment

1. `frontend/src/App.jsx` holds the scenario, report, loading state, error, and interface locale. Sample mode returns authored sample data; API mode calls the backend.
2. `frontend/src/lib/api.js` sends `POST /api/assess` with `scenario` and `response_language`. It applies input limits, a 60-second client deadline, and safe error mapping. `assessmentSchema.js` checks the response before the UI displays it.
3. `backend/app/api/routes.py` receives the request. Pydantic models in `schemas.py` trim and validate the input and language. The route applies rate limiting and calls `pipeline.assess`.
4. `backend/app/pipeline.py` runs input guardrails before sending the sanitized scenario to the selected agent. It later applies output checks, builds review activity, and writes the audit event.
5. `backend/app/agent/gemini.py` manages the live Gemini tool-use loop. `prompt.py` defines the assessment instructions and response language. The model selects local tools; the backend executes them and sends their results back to the model.
6. `backend/app/agent/tools.py` exposes the requirement catalog, requirement-specific guidance, and deterministic risk scanning. These tools read local data and cannot execute scenario instructions or fetch arbitrary URLs.
7. After the three context tools succeed, Gemini can call `submit_assessment`. Its arguments must validate as `AgentAssessment`. A tool-call schema helps enforce structure; it does not guarantee factual correctness.
8. `backend/app/guardrails/` checks evidence, requirement coverage, and policy rules. It can correct statuses and raise risk to a policy minimum, but cannot prove full compliance.
9. The pipeline returns eight findings, a summary, risk rationale, next actions, questions, actual review steps, guardrail notes, model information, and report language. React renders these as text and can export the result as JSON.

The optional Anthropic adapter implements the same runner interface. It is not a silent fallback for Gemini.

## The agentic part

A chatbot would send text to a model and display its answer. Here the model requests specific capabilities, receives tool results, and constructs a typed assessment from the scenario and policy context. The application controls the tool implementations, permitted operations, time budget, and final checks. The review activity records actual tool calls rather than model-written claims about actions.

## What comes from AI and what comes from code

| Model judgment | Deterministic application behavior |
| --- | --- |
| Interpret the proposed use case | Validate input size and requested language |
| Select tools and guidance | Execute only registered local tools |
| Explain relevance of scenario facts | Check requirement IDs and coverage |
| Propose findings and risk | Verify excerpts against the sanitized source |
| Recommend actions and questions | Apply policy checks and expose corrections |
| Generate narrative in the selected language | Localize authored messages and record the actual workflow |

A quote existing in the scenario does not prove it supports a finding. Human review is essential.

## Status and uncertainty

- `supported`: scenario evidence supports the requirement; this is not certification.
- `gap`: supplied facts explicitly conflict with the requirement.
- `needs_clarification`: the description is insufficient to establish the control.
- `not_applicable`: the requirement does not apply, with an explanation.

Risk describes potential impact, not the amount of missing documentation. A vague scenario can remain unknown risk. Missing controls must not automatically be treated as proven violations.

## Data, language, and secrets

Provider credentials stay in ignored `backend/.env`. The frontend receives no provider key. Input redaction reduces disclosure risks but is heuristic and cannot detect every sensitive value. Audit events contain metadata and a scenario hash rather than raw scenario text. The application does not save scenario history in browser storage.

The request language controls narrative generation and server-authored messages. Evidence stays in the sanitized source language. Existing results keep their generation language; switching the interface offers reassessment. English and Arabic catalogs are separate from rendering and assessment logic. Input risk and injection heuristics are primarily English.

## How to verify and explain it

Start with the root README's commands. Run the deterministic tests before making a live provider call. Tests with scripted clients establish contract handling and guardrail behavior; they do not establish model quality. The separate live check and README screenshots document observed live behavior on fictional scenarios.

For a practical walkthrough, use the customer support scenario: identify AI-003's human review evidence, explain why missing vendor assessment information needs clarification, expand the actual review activity, and export the report. Then use the employee-decision scenario to explain why consequential automated decisions require greater scrutiny.

Be prepared to explain the choices and limitations: why a fixed catalog is sufficient for eight requirements; why no vector database is needed; why the key is server-side; how evidence matching differs from semantic verification; why provider failure returns an error instead of fake results; and why production use would need authentication, shared rate limiting, and stronger monitoring.
