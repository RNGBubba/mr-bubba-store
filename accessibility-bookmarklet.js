/* Local-only accessibility QA bookmarklet.
 * It inspects the current document and does not fetch, upload, or store results.
 */
(function () {
  const findings = [];
  const add = (rule, message, count) => findings.push({ rule, message, count });
  const doc = document;
  const images = [...doc.querySelectorAll('img')];
  add('IMG-ALT', 'Images without an alt attribute', images.filter((x) => !x.hasAttribute('alt')).length);
  const headings = [...doc.querySelectorAll('h1,h2,h3,h4,h5,h6')];
  let previous = 0;
  let headingJumps = 0;
  headings.forEach((h) => { const level = Number(h.tagName.slice(1)); if (previous && level > previous + 1) headingJumps += 1; previous = level; });
  add('HEADING-ORDER', 'Heading jumps greater than one level', headingJumps);
  const controls = [...doc.querySelectorAll('input:not([type="hidden"]),select,textarea,button')];
  const hasName = (x) => x.getAttribute('aria-label') || x.getAttribute('aria-labelledby') || (x.labels && x.labels.length) || x.textContent.trim() || (x.tagName === 'INPUT' && x.value.trim());
  add('FORM-LABEL', 'Controls without a common accessible-name signal', controls.filter((x) => !hasName(x)).length);
  add('EMPTY-LINK', 'Links without text or an accessible name', [...doc.querySelectorAll('a')].filter((x) => !x.textContent.trim() && !x.getAttribute('aria-label') && !x.getAttribute('aria-labelledby')).length);
  add('LANG', 'Document without a non-empty lang attribute', doc.documentElement.getAttribute('lang')?.trim() ? 0 : 1);
  const ids = [...doc.querySelectorAll('[id]')].map((x) => x.id);
  add('DUPLICATE-ID', 'Duplicate id values', ids.length - new Set(ids).size);
  add('TABINDEX', 'Positive tabindex values needing review', [...doc.querySelectorAll('[tabindex]')].filter((x) => Number(x.getAttribute('tabindex')) > 0).length);
  add('BUTTON-NAME', 'Buttons without visible text or an accessible name', [...doc.querySelectorAll('button')].filter((x) => !x.textContent.trim() && !x.getAttribute('aria-label') && !x.getAttribute('aria-labelledby')).length);
  add('VIEWPORT', 'Missing effective responsive viewport meta element', [...doc.querySelectorAll('meta[name="viewport"]')].some((x) => /width\s*=\s*device-width/i.test(x.getAttribute('content') || '')) ? 0 : 1);
  add('LANDMARK', 'Document without a main landmark', doc.querySelector('main,[role="main"]') ? 0 : 1);
  const lines = findings.map((x) => `${x.rule}: ${x.count} — ${x.message}`);
  const report = lines.join('\n');
  window.alert(report);
})();
