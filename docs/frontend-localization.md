# Frontend localization

English and Arabic are registered in `frontend/src/i18n/config.js`. UI messages use semantic keys in separate UTF-8 JSON catalogs under `i18n/locales/`. Components call `useI18n()` and never decide which language to render themselves.

## Add a language

1. Copy `en.json` to a new locale catalog and translate every value, preserving keys and interpolation placeholders.
2. Import the catalog and register its language code, native label, direction (`ltr` or `rtl`), and messages in `config.js`.
3. Run `node --test tests/i18n.test.js` from `frontend/`, then build and lint. The tests check every registered language automatically.
4. Visually review mobile and desktop layouts in that language.

The switcher derives its options from the registry. Unknown/missing messages fall back to English. `t(key, { name: value })` supports named `{name}` placeholders without HTML injection; use complete sentences instead of joining translated fragments. `formatNumber` uses `Intl.NumberFormat`.

The provider sets document `lang`, `dir`, and title; it remembers only the language preference in localStorage. Blocked storage does not prevent switching. A supported stored preference wins over the browser's language; otherwise English is the fallback.

RTL uses logical CSS spacing, Arabic-friendly typography, mirrored directional icons, and isolated requirement/reference IDs. User input and live model text use automatic text direction. Language changes preserve user input.

Authored scenarios, requirements, sample findings, errors, accessible labels, and navigation are localized. The fixed sample report switches languages immediately, including evidence that matches the translated sample scenario. Live backend content is displayed as returned: translating evidence after generation could change its meaning. Localizing model-generated analysis requires an explicit backend response-language contract and corresponding end-to-end validation; the current API request is unchanged.
