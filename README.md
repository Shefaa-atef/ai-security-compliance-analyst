# AI Security & Compliance Analyst

An AI-powered application for assessing security and compliance scenarios with structured findings, supporting evidence, risk identification, and recommended actions.

## Project status

React + Vite frontend initialized with the standard framework starter. The assessment application and Python backend have not been implemented yet.

## Repository structure

```text
ai-security-compliance-analyst/
  frontend/     React user interface
  backend/      Python API and assessment workflow
  README.md     Project overview
  .gitignore    Shared exclusions for local files and secrets
```

The frontend and backend live in one Git repository with separate dependencies and configuration. The React interface will call the Python backend over HTTP. AI provider credentials belong only in the backend environment.

See [frontend setup notes](frontend/README.md) for development commands and [backend setup notes](backend/README.md) for the planned API scope.

Development will proceed through incremental commits. Setup instructions and application screenshots will be added as functionality is implemented.
