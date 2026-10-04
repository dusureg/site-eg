/* Runs in <head>, before the page paints.
   1. applies the saved (or system) theme, so there is no light/dark flash
   2. sends a returning visitor to the language they picked last time
   Search engines have no saved choice, so they always see the page they requested. */
(function () {
  var d = document.documentElement;
  d.className += ' js';
  try {
    var s = localStorage, t = s.getItem('dusur-theme');
    if (t !== 'light' && t !== 'dark') t = matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    d.setAttribute('data-theme', t);
    var m = document.querySelector('meta[name=theme-color]');
    if (m) m.content = t === 'light' ? '__LIGHT__' : '__DARK__';
    var l = s.getItem('dusur-lang');
    if ((l === 'ar' || l === 'en') && l !== d.getAttribute('data-lang') && d.getAttribute('data-alt')) {
      location.replace(d.getAttribute('data-alt') + location.hash);
    }
  } catch (e) {
    d.setAttribute('data-theme', 'dark');
  }
})();
