(function () {
  'use strict';

  var tabs = Array.prototype.slice.call(document.querySelectorAll('[data-news-tab]'));
  var panels = {
    news: document.getElementById('news-panel'),
    gallery: document.getElementById('gallery-panel')
  };
  var filters = Array.prototype.slice.call(document.querySelectorAll('[data-news-filter]'));

  function setTab(name) {
    tabs.forEach(function (tab) {
      var active = tab.getAttribute('data-news-tab') === name;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', String(active));
    });
    Object.keys(panels).forEach(function (key) {
      if (panels[key]) panels[key].hidden = key !== name;
    });
    applyFilter();
  }

  function applyFilter() {
    var active = document.querySelector('[data-news-filter].is-active');
    var year = active ? active.getAttribute('data-news-filter') : 'all';
    var visiblePanel = document.querySelector('.news-panel:not([hidden]), .gallery-panel:not([hidden])');
    if (!visiblePanel) return;

    var entries = Array.prototype.slice.call(visiblePanel.querySelectorAll('[data-news-year]'));
    var shown = 0;
    entries.forEach(function (entry) {
      var show = year === 'all' || entry.getAttribute('data-news-year') === year;
      entry.hidden = !show;
      if (show) shown += 1;
    });

    var empty = visiblePanel.querySelector('.news-empty');
    if (empty) empty.hidden = shown > 0;
  }

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () { setTab(tab.getAttribute('data-news-tab')); });
  });

  filters.forEach(function (filter) {
    filter.addEventListener('click', function () {
      filters.forEach(function (item) {
        item.classList.remove('is-active');
        item.setAttribute('aria-pressed', 'false');
      });
      filter.classList.add('is-active');
      filter.setAttribute('aria-pressed', 'true');
      applyFilter();
    });
  });
})();
