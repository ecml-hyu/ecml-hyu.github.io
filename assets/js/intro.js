/* Show the ECML intro once per browser session; ?intro=1 always previews it. */
(function () {
  'use strict';

  var key = 'ecml-intro-seen';
  var forcePreview = /(?:^|[?&])intro=1(?:&|$)/.test(window.location.search);
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var seen = false;

  try {
    seen = window.sessionStorage.getItem(key) === '1';
  } catch (error) {
    seen = false;
  }

  if (reduceMotion || (seen && !forcePreview)) {
    document.documentElement.classList.add('intro-seen');
    document.addEventListener('DOMContentLoaded', function () {
      document.getElementById('intro')?.remove();
    }, { once: true });
    return;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var intro = document.getElementById('intro');
    if (!intro) return;

    var splineViewer = intro.querySelector('spline-viewer[data-spline-url]');
    if (splineViewer && !splineViewer.hasAttribute('url')) {
      splineViewer.setAttribute('url', splineViewer.dataset.splineUrl);
    }

    var background = [
      document.querySelector('body > header'),
      document.querySelector('body > main'),
      document.querySelector('body > footer')
    ].filter(Boolean);
    var previousHtmlOverflow = document.documentElement.style.overflow;
    var previousBodyOverflow = document.body.style.overflow;
    var opening = false;

    background.forEach(function (element) { element.inert = true; });
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';

    var closeIntro = function () {
      if (opening) return;
      opening = true;
      document.removeEventListener('keydown', onKeydown);
      intro.dispatchEvent(new CustomEvent('intro:close'));
      intro.classList.add('open');

      try {
        window.sessionStorage.setItem(key, '1');
      } catch (error) {
        /* A blocked session store must not prevent entry to the site. */
      }

      window.setTimeout(function () {
        if (splineViewer && typeof splineViewer.unload === 'function') {
          splineViewer.unload();
        }
        intro.remove();
        background.forEach(function (element) { element.inert = false; });
        document.documentElement.style.overflow = previousHtmlOverflow;
        document.body.style.overflow = previousBodyOverflow;
        var destination = document.querySelector('main');
        if (destination) {
          destination.setAttribute('tabindex', '-1');
          destination.focus({ preventScroll: true });
          destination.addEventListener('blur', function () {
            destination.removeAttribute('tabindex');
          }, { once: true });
        }
      }, 800);
    };

    var onKeydown = function (event) {
      if (event.key === 'Escape') closeIntro();
    };

    var enter = document.getElementById('enter-site');
    if (enter) {
      enter.addEventListener('click', closeIntro);
      enter.focus({ preventScroll: true });
      document.addEventListener('keydown', onKeydown);
    }
  });
})();
