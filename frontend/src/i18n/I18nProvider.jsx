import { useEffect, useMemo, useState } from "react";
import { I18nContext } from "./context";
import { defaultLocale, locales, translate } from "./config";
const storageKey = "acme.locale";
function initialLocale() {
  try {
    const saved = localStorage.getItem(storageKey);
    if (Object.hasOwn(locales, saved)) return saved;
  } catch {
    /* Language switching also works when browser storage is blocked. */
  }
  const preferred = navigator.language?.split("-")[0];
  return Object.hasOwn(locales, preferred) ? preferred : defaultLocale;
}
export default function I18nProvider({ children }) {
  const [locale, setLocale] = useState(initialLocale);
  const value = useMemo(
    () => ({
      locale,
      direction: locales[locale].direction,
      setLocale: (next) => {
        if (Object.hasOwn(locales, next)) setLocale(next);
      },
      t: (key, values) => translate(locale, key, values),
      formatNumber: (number) => new Intl.NumberFormat(locale).format(number),
    }),
    [locale],
  );
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locales[locale].direction;
    document.title = translate(locale, "app.title");
    try {
      localStorage.setItem(storageKey, locale);
    } catch {
      /* Optional preference storage. */
    }
  }, [locale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
