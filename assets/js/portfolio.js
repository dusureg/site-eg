/* Dusur — "Our work": sector filters and the project preview window.
   Loaded on demand by main.js (a separate file, so first load stays small).
   All text comes from the page itself, so this file works unchanged in Arabic and English. */

export function init(work) {
  const d = document, root = d.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rtl = root.dir === 'rtl';
  const grid = work.querySelector('#projects');
  const cards = [...grid.children];
  const chips = [...work.querySelectorAll('.chip')];
  const count = work.querySelector('.count');
  const empty = work.querySelector('.empty');
  const dlg = d.getElementById('pv');
  const toast = d.querySelector('.toast');
  let visible = cards.slice(), lastTrigger = null, toastTimer = 0;

  const slot = (n) => dlg.querySelector(`[data-slot="${n}"]`);
  const idFromHash = () => (location.hash.match(/^#project-(.+)$/) || [])[1] || '';
  const ready = (img) => { img.classList.add('is-loaded'); img.closest('.media')?.classList.add('is-ready'); };

  /* ── filters ───────────────────────────────────────────────────────── */
  function filter(id) {
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.filter === id)));
    visible = [];
    cards.forEach((c) => {
      const show = id === 'all' || c.dataset.sector === id;
      c.hidden = !show;
      c.classList.remove('enter');
      if (show) visible.push(c);
    });
    if (!reduce) {
      requestAnimationFrame(() => visible.forEach((c, i) => {
        c.style.setProperty('--i', Math.min(i, 8));
        c.classList.add('enter');
        c.addEventListener('animationend', (e) => { if (e.target === c) c.classList.remove('enter'); }, { once: true });
      }));
    }
    count.textContent = count.dataset.tpl.replace('{n}', visible.length);
    empty.hidden = visible.length > 0;
  }
  chips.forEach((c) => c.addEventListener('click', () => filter(c.dataset.filter)));
  count.textContent = count.dataset.tpl.replace('{n}', cards.length);

  /* ── "coming soon" state for projects without a file ───────────────── */
  d.addEventListener('click', (e) => {
    const b = e.target.closest('[data-soon]');
    if (!b) return;
    toast.textContent = work.dataset.toast;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 3200);
  });

  /* ── preview window ────────────────────────────────────────────────── */
  function fill(card) {
    const src = card.querySelector('template.pv-src').content;
    const media = card.querySelector('.media').cloneNode(true);
    media.classList.remove('is-ready');
    media.querySelectorAll('img, source').forEach((n) => { n.sizes = '(min-width: 820px) 600px, 94vw'; });
    media.querySelectorAll('img').forEach((i) => { i.removeAttribute('loading'); i.classList.remove('is-loaded'); });
    slot('media').replaceChildren(media);
    media.querySelectorAll('img.media__img').forEach((i) => (i.complete && i.naturalWidth ? ready(i) : i.addEventListener('load', () => ready(i), { once: true })));

    slot('tags').replaceChildren(...[...card.querySelectorAll('.tags > *')].map((n) => n.cloneNode(true)));
    slot('title').textContent = card.querySelector('h3').textContent;
    slot('desc').textContent = card.querySelector('.card__body > p').textContent;
    slot('hl').replaceChildren(src.querySelector('ul').cloneNode(true));

    const note = src.querySelector('.note');
    slot('note').hidden = !note;
    slot('note').textContent = note ? note.textContent : '';

    const foot = slot('foot');
    foot.replaceChildren(card.querySelector('.actions > :not([data-preview])').cloneNode(true));
    src.querySelectorAll('a').forEach((a) => foot.append(a.cloneNode(true)));
  }

  function show(id, push) {
    const card = cards.find((c) => c.dataset.id === id);
    if (!card) return;
    if (card.hidden) filter('all');
    fill(card);
    if (!dlg.open) { dlg.showModal(); root.classList.add('pv-open'); }
    dlg.scrollTop = 0;
    const url = '#project-' + id;
    if (push) history.pushState({ pv: id }, '', url);
    else if (location.hash !== url) history.replaceState(history.state, '', url);
  }

  function hide() {
    if (!dlg.open) return;
    const done = () => {
      dlg.classList.remove('closing');
      dlg.close();
      root.classList.remove('pv-open');
      if (lastTrigger) lastTrigger.focus({ preventScroll: true });
    };
    if (reduce) done(); else { dlg.classList.add('closing'); setTimeout(done, 220); }
  }

  function requestClose() {
    if (history.state && history.state.pv) history.back();          // pops the entry we pushed
    else {
      hide();
      if (idFromHash()) history.replaceState(null, '', location.pathname + location.search);
    }
  }

  function step(dir) {
    const cur = slot('title').textContent;
    let i = visible.findIndex((c) => c.querySelector('h3').textContent === cur);
    i = (i + dir + visible.length) % visible.length;
    show(visible[i].dataset.id, false);
  }

  grid.addEventListener('click', (e) => {
    const a = e.target.closest('[data-preview]');
    if (!a) return;
    e.preventDefault();
    lastTrigger = a;
    show(a.dataset.preview, true);
  });
  dlg.addEventListener('click', (e) => {
    if (e.target === dlg || e.target.closest('[data-close]')) return requestClose();
    const s = e.target.closest('[data-step]');
    if (s) step(Number(s.dataset.step));
  });
  dlg.addEventListener('cancel', (e) => { e.preventDefault(); requestClose(); });
  dlg.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') step(rtl ? -1 : 1);
    if (e.key === 'ArrowLeft') step(rtl ? 1 : -1);
  });
  addEventListener('popstate', () => { const id = idFromHash(); if (id) show(id, false); else hide(); });

  /* a shared link such as  …/#project-oak-family-kitchen  opens straight away */
  const first = idFromHash();
  if (first) show(first, false);
}
