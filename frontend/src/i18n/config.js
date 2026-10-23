import en from "./locales/en.json" with { type: "json" };
import ar from "./locales/ar.json" with { type: "json" };
// Add a catalog and one entry here to register another language.
export const locales = {
  en: { label: "English", direction: "ltr", messages: en },
  ar: { label: "العربية", direction: "rtl", messages: ar },
};
export const defaultLocale = "en";
export function translate(locale, key, values = {}) {
  const message =
    locales[locale]?.messages[key] ??
    locales[defaultLocale].messages[key] ??
    key;
  return message.replace(/\{(\w+)\}/g, (match, name) =>
    values[name] == null ? match : String(values[name]),
  );
}
