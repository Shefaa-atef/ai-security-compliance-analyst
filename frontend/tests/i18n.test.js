import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";
import { locales, translate } from "../src/i18n/config.js";
import { getLocalizedSample } from "../src/data/localizedSample.js";

test("all registered locales have complete, nonempty catalogs and matching placeholders", () => {
  const referenceKeys = Object.keys(locales.en.messages).sort();
  for (const language of Object.values(locales)) {
    assert.deepEqual(Object.keys(language.messages).sort(), referenceKeys);
    for (const key of referenceKeys) {
      assert.equal(typeof language.messages[key], "string");
      assert.ok(language.messages[key].trim(), key);
      const placeholders = (text) =>
        [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
      assert.deepEqual(
        placeholders(language.messages[key]),
        placeholders(locales.en.messages[key]),
        key,
      );
    }
  }
});

test("unknown locale falls back to English and unknown keys remain diagnosable", () => {
  assert.equal(
    translate("unregistered", "form.heading"),
    locales.en.messages["form.heading"],
  );
  assert.equal(translate("ar", "missing.key"), "missing.key");
});

test("localized sample evidence remains verbatim in its localized scenario", () => {
  for (const locale of Object.keys(locales)) {
    const t = (key) => translate(locale, key);
    const sample = getLocalizedSample(t);
    assert.equal(sample.findings.length, 8);
    for (const finding of sample.findings) {
      for (const quote of finding.evidence)
        assert.ok(
          t("scenarios.support.text").includes(quote),
          `${locale}: ${quote}`,
        );
    }
  }
});

test("the actual screen and populated report render in every registered language", async () => {
  const server = await createServer({
    server: { middlewareMode: true },
    appType: "custom",
  });
  try {
    const { default: App } = await server.ssrLoadModule("/src/App.jsx");
    const { default: Report } = await server.ssrLoadModule(
      "/src/components/AssessmentReport.jsx",
    );
    const { I18nContext } = await server.ssrLoadModule("/src/i18n/context.js");
    for (const [locale, language] of Object.entries(locales)) {
      const t = (key) => translate(locale, key);
      const value = {
        locale,
        direction: language.direction,
        setLocale() {},
        t,
        formatNumber: (number) => new Intl.NumberFormat(locale).format(number),
      };
      const wrap = (child) =>
        createElement(I18nContext.Provider, { value }, child);
      const screen = renderToStaticMarkup(wrap(createElement(App)));
      assert.ok(screen.includes(t("form.heading")));
      assert.ok(screen.includes(t("language.label")));
      assert.ok(screen.includes(t("scenarios.support.title")));
      const report = renderToStaticMarkup(
        wrap(
          createElement(Report, {
            result: {
              ...getLocalizedSample(t),
              isSample: true,
              guardrail_notes: ["<script>alert(1)</script>"],
              model: "test-model",
            },
            loading: false,
            reportRef: null,
          }),
        ),
      );
      assert.ok(report.includes(t("sample.summary")));
      assert.ok(report.includes(t("requirements.AI-001.title")));
      assert.ok(report.includes(t("status.needs_clarification")));
      assert.ok(report.includes(t("report.guardrails")));
      assert.ok(report.includes("test-model"));
      assert.ok(report.includes("&lt;script&gt;"));
      assert.ok(!report.includes("<script>alert(1)</script>"));
    }
  } finally {
    await server.close();
  }
});
