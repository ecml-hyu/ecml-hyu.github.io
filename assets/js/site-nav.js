(function () {
  'use strict';

  var nav = document.querySelector('.site-nav');
  var toggle = nav && nav.querySelector('.nav-toggle');
  var menu = nav && nav.querySelector('.links');
  var compact = window.matchMedia('(max-width: 960px)');

  if (!nav || !toggle || !menu) return;

  var setOpen = function (open, restoreFocus) {
    var shouldOpen = compact.matches && open;
    nav.classList.toggle('is-menu-open', shouldOpen);
    toggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    toggle.setAttribute('aria-label', shouldOpen ? 'Close navigation' : 'Open navigation');
    menu.hidden = compact.matches ? !shouldOpen : false;
    if (restoreFocus) toggle.focus({ preventScroll: true });
  };

  var syncBreakpoint = function () {
    nav.classList.add('is-nav-ready');
    setOpen(false, false);
  };

  toggle.addEventListener('click', function () {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true', false);
  });

  menu.addEventListener('click', function (event) {
    if (event.target.closest('a')) setOpen(false, false);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setOpen(false, true);
    }
  });

  document.addEventListener('pointerdown', function (event) {
    if (toggle.getAttribute('aria-expanded') === 'true' && !nav.contains(event.target)) {
      setOpen(false, false);
    }
  });

  compact.addEventListener?.('change', syncBreakpoint);
  syncBreakpoint();

  var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  if (finePointer.matches && !reducedMotion.matches) {
    var cursor = document.createElement('span');
    cursor.className = 'ecml-cursor';
    cursor.setAttribute('aria-hidden', 'true');
    document.body.appendChild(cursor);

    var cursorReady = false;
    var interactiveSelector = 'a, button, [role="button"], input, select, textarea, summary, [tabindex]:not([tabindex="-1"])';

    window.addEventListener('pointermove', function (event) {
      if (!cursorReady) {
        document.documentElement.classList.add('ecml-cursor-active');
        cursorReady = true;
      }

      cursor.style.transform = 'translate3d(' + (event.clientX - 14) + 'px,' + (event.clientY - 14) + 'px,0)';
      cursor.classList.add('is-visible');
      var target = event.target instanceof Element ? event.target : null;
      cursor.classList.toggle('is-interactive', Boolean(target && target.closest(interactiveSelector)));
    }, { passive: true });

    document.addEventListener('pointerdown', function () {
      cursor.classList.add('is-down');
    }, { passive: true });

    document.addEventListener('pointerup', function () {
      cursor.classList.remove('is-down');
    }, { passive: true });

    document.addEventListener('pointerleave', function () {
      cursor.classList.remove('is-visible', 'is-down');
    });

    window.addEventListener('blur', function () {
      cursor.classList.remove('is-visible', 'is-down');
    });

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) cursor.classList.remove('is-visible', 'is-down');
    });
  }
})();
