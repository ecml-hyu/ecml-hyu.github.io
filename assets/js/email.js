/* Reveal an obfuscated address on the first activation, then copy it. */
(function () {
  'use strict';

  var controls = document.querySelectorAll('.email-link');
  if (!controls.length) return;

  var status = document.createElement('span');
  status.className = 'visually-hidden';
  status.setAttribute('aria-live', 'polite');
  document.body.appendChild(status);

  function fallbackCopy(value) {
    var field = document.createElement('textarea');
    field.value = value;
    field.setAttribute('readonly', '');
    field.style.position = 'fixed';
    field.style.opacity = '0';
    document.body.appendChild(field);
    field.select();
    var copied = document.execCommand('copy');
    document.body.removeChild(field);
    return copied;
  }

  function copyAddress(value) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(value);
    }
    return fallbackCopy(value) ? Promise.resolve() : Promise.reject(new Error('Copy failed'));
  }

  Array.prototype.forEach.call(controls, function (control) {
    var user = control.getAttribute('data-user');
    var domain = control.getAttribute('data-domain');
    if (!user || !domain) return;

    var address = user + '@' + domain;
    control.setAttribute('title', 'Reveal email address');
    control.setAttribute('aria-label', 'Reveal email address');

    control.addEventListener('click', function (event) {
      event.preventDefault();

      if (control.dataset.revealed !== 'true') {
        control.dataset.revealed = 'true';
        control.textContent = address;
        control.setAttribute('title', 'Copy ' + address);
        control.setAttribute('aria-label', 'Copy ' + address);
        status.textContent = 'Email address revealed. Activate again to copy.';
        return;
      }

      copyAddress(address).then(function () {
        control.classList.add('is-copied');
        control.textContent = 'Copied ✓';
        status.textContent = address + ' copied to clipboard.';
        window.setTimeout(function () {
          control.classList.remove('is-copied');
          control.textContent = address;
        }, 1400);
      }).catch(function () {
        status.textContent = 'Copy was unavailable. The email address is ' + address + '.';
      });
    });
  });
})();
