/* Dusur — page behaviour. Inlined into every page (about 3 KB minified).
   The portfolio code (filters + preview window) lives in portfolio.js and is only
   downloaded when the visitor gets near "Our work".                                   */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); };
  var save = function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} };
  var saved = function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } };
  var activeId = '';
  var onMQ = function (mq, fn) { if (mq.addEventListener) mq.addEventListener('change', fn); else if (mq.addListener) mq.addListener(fn); };

  /* ── theme ─────────────────────────────────────────────────────────── */
  var themeBtn = $('.theme-btn'), meta = $('meta[name=theme-color]');
  function paintTheme(t) {
    root.setAttribute('data-theme', t);
    if (meta) meta.content = t === 'light' ? '__LIGHT__' : '__DARK__';
    if (themeBtn) themeBtn.setAttribute('aria-label', t === 'light' ? themeBtn.getAttribute('data-to-dark') : themeBtn.getAttribute('data-to-light'));
  }
  paintTheme(root.getAttribute('data-theme') || 'dark');
  function switchTheme(next, remember) {
    if (!reduce) { root.classList.add('theming'); setTimeout(function () { root.classList.remove('theming'); }, 650); }
    paintTheme(next);
    if (remember) save('dusur-theme', next);
  }
  if (themeBtn) themeBtn.addEventListener('click', function () {
    switchTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light', true);
  });
  // follow the system setting until the visitor makes their own choice
  onMQ(matchMedia('(prefers-color-scheme: light)'), function (e) {
    if (!saved('dusur-theme')) switchTheme(e.matches ? 'light' : 'dark', false);
  });

  /* ── language: remember the choice, keep the reader's place ────────── */
  $$('.seg a').forEach(function (a) {
    a.addEventListener('click', function () {
      save('dusur-lang', a.getAttribute('data-lang'));
      if (a.getAttribute('aria-current') === 'true') return;
      var h = location.hash && location.hash.length > 1 ? location.hash : (activeId ? '#' + activeId : '');
      a.href = a.getAttribute('href').split('#')[0] + h;
    });
  });

  /* ── mobile menu ───────────────────────────────────────────────────── */
  var menuBtn = $('.menu-btn'), nav = $('#nav');
  function setMenu(open) {
    nav.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    menuBtn.setAttribute('aria-label', menuBtn.getAttribute(open ? 'data-close' : 'data-open'));
  }
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function () { setMenu(!nav.classList.contains('open')); });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && nav.classList.contains('open')) { setMenu(false); menuBtn.focus(); } });
    d.addEventListener('click', function (e) { if (nav.classList.contains('open') && !e.target.closest('.site-header')) setMenu(false); });
    onMQ(matchMedia('(min-width: 980px)'), function () { setMenu(false); });
  }

  /* ── header state, reading progress, header height ─────────────────── */
  var header = $('.site-header'), bar = $('.progress'), ticking = false;
  function measure() { if (header) root.style.setProperty('--hh', header.offsetHeight + 'px'); }
  measure();
  addEventListener('resize', measure);
  function onScroll() {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () {
      var y = window.scrollY || root.scrollTop, max = root.scrollHeight - innerHeight;
      if (header) header.classList.toggle('scrolled', y > 12);
      if (bar) bar.style.setProperty('--p', max > 0 ? Math.min(1, y / max) : 0);
      if (y < 80) { activeId = ''; $$('.nav a.on').forEach(function (a) { a.classList.remove('on'); }); }
      ticking = false;
    });
  }
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── highlight the section being read ──────────────────────────────── */
  var links = {};
  $$('.nav a[href^="#"]').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
  if ('IntersectionObserver' in window) {
    var spy = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        activeId = e.target.id;
        $$('.nav a.on').forEach(function (a) { a.classList.remove('on'); });
        if (links[activeId]) links[activeId].classList.add('on');
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    Object.keys(links).forEach(function (id) { var s = d.getElementById(id); if (s) spy.observe(s); });

    /* ── gentle reveal as sections scroll in (once per element) ──────── */
    if (!reduce) {
      var items = $$('.section .section__head, .why__grid > *, .svc, .cards > *, .band, .steps > *, .section .cta-row, .contact__box');
      var seen = [];
      items.forEach(function (el) {
        if (seen.indexOf(el) > -1 || el.closest('#work')) return;
        seen.push(el);
        el.classList.add('rv');
        el.style.transitionDelay = Math.min([].indexOf.call(el.parentNode.children, el), 5) * 80 + 'ms';
      });
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!e.isIntersecting) return;
          var el = e.target; el.classList.add('in'); io.unobserve(el);
          setTimeout(function () { el.classList.remove('rv', 'in'); el.style.transitionDelay = ''; }, 1600);
        });
      }, { threshold: .1, rootMargin: '0px 0px -6% 0px' });
      seen.forEach(function (el) { io.observe(el); });
    }
  }

  /* ── images: fade the real photo in over the drawing, no layout shift ─ */
  function ready(img) {
    img.classList.add('is-loaded');
    var f = img.closest('.media'); if (f) f.classList.add('is-ready');
  }
  $$('img.media__img').forEach(function (img) {
    if (img.complete && img.naturalWidth) ready(img);
    else img.addEventListener('load', function () { ready(img); }, { once: true });
  });

  /* ── portfolio: load its code only when it is about to be needed ───── */
  var work = $('#work'), asked = false;
  function loadWork() {
    if (asked) return; asked = true;
    import(__BASE__ + '__PORTFOLIO__').then(function (m) { m.init(work); }).catch(function (e) { asked = false; if (window.console) console.warn('Dusur: could not load the portfolio code', e); });
  }
  if (work) {
    if (/^#project-/.test(location.hash) || !('IntersectionObserver' in window)) loadWork();
    else {
      new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { loadWork(); o.disconnect(); } }, { rootMargin: '700px 0px' }).observe(work);
      work.addEventListener('pointerover', loadWork, { once: true });
    }
  }
})();
