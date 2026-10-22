// Client-side ko/en switch. Block content (articles, labels) is shown/hidden by CSS from html[data-lang];
// this swaps the strings CSS cannot reach: SVG chart text, <title> tooltips and aria-labels.
// The key 'lang' is also read by the inline head script in Base.astro (before first paint).
export type Lang = 'en' | 'ko';
const KEY = 'lang';

export function applyLang(lang: Lang) {
  const html = document.documentElement;
  html.lang = lang;
  html.dataset.lang = lang;
  document.querySelectorAll<HTMLElement | SVGElement>('[data-ko]').forEach((el) => {
    const s = el.dataset[lang];
    if (s != null) el.textContent = s;
  });
  document.querySelectorAll('[data-ko-label]').forEach((el) => {
    const s = el.getAttribute(`data-${lang}-label`);
    if (s != null) el.setAttribute('aria-label', s);
  });
  document.querySelectorAll('[data-set-lang]').forEach((b) =>
    b.setAttribute('aria-pressed', String(b.getAttribute('data-set-lang') === lang)),
  );
}

export function initLang() {
  let stored: string | null = null;
  try { stored = localStorage.getItem(KEY); } catch {}
  applyLang(stored === 'ko' ? 'ko' : 'en');
  document.querySelectorAll<HTMLButtonElement>('[data-set-lang]').forEach((b) =>
    b.addEventListener('click', () => {
      const lang = b.dataset.setLang === 'ko' ? 'ko' : 'en';
      applyLang(lang);
      try { localStorage.setItem(KEY, lang); } catch {}
    }),
  );
}
