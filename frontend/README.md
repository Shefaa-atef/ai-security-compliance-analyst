# Frontend

React + Vite, JavaScript. The interface uses system fonts and local SVG icons; no external font or image requests.

## Run

```powershell
cd frontend
npm install
npm run dev
```

Open the address printed by Vite. Run `npm run build` and `npm run lint` for checks.

## Modes

- **Sample preview** displays a fixed customer support report. It makes no AI call and does not assess custom input.
- **Assess a scenario** sends input to `POST /api/assess`. The Python backend must be running. The frontend validates the response before displaying it.

Vite proxies `/api` to `http://127.0.0.1:8000`. To use another backend, copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL`, then restart Vite. All `VITE_` values are public: never place provider credentials there. In production, configure an API reverse proxy or an explicit backend URL and appropriate CORS.

## Organization

- `src/components/`: one UI component per file.
- `src/data/`: requirements, example scenarios, and the explicitly labeled sample report.
- `src/lib/api.js`: network requests, timeout, and response validation.
- `src/App.jsx`: shared state and orchestration.
- `src/index.css`: global tokens and base styles.
- `src/App.css`: page width, workspace columns, and footer only.
- `src/components/*.css`: styles and responsive rules beside the component that owns them.
- `src/styles/shared.css`: shared panel primitives, badges, and animations.
- `src/styles/rtl.css`: direction-specific typography and icons.

Findings expand using native keyboard-accessible disclosure controls. Results are rendered as text, never injected HTML. Reports can be exported as JSON. No scenario history is saved to browser storage.

See [backend handoff](../docs/backend-handoff.md) for the complete contract and backend implementation plan.

## Languages

English and Arabic are available from the header language selector, including right-to-left layout and translated sample content. Live requests include `response_language`; narrative follows that language while evidence stays in the original scenario language. Existing results retain their recorded language, with a reassessment action after switching languages. See [localization notes](../docs/frontend-localization.md) for adding languages and the distinction between UI translation and live model output.

Run localization checks from this folder with `node --test tests/i18n.test.js`.

## API response handling

`src/lib/assessmentSchema.js` validates required findings and optional guardrail/model metadata. `src/lib/api.js` handles requests, safe localized error codes, cancellation deadlines, and input limits. Guardrail observations are visible in the report, so backend corrections are not hidden from the reviewer. `npm test` runs the API and localization checks.
