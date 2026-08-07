/*
 * Publications 탭.
 *
 * 점진적 향상 방식이다. HTML 만으로는 세 묶음이 모두 펼쳐진 채 보이고,
 * 이 스크립트가 실행되면 그때부터 탭으로 접힌다.
 * JS 가 꺼져 있어도 내용을 전부 읽을 수 있다.
 *
 * 주소에 #patents 처럼 붙이면 그 탭이 열린 채로 시작한다.
 * 탭을 바꾸면 주소도 따라 바뀌어(history.replaceState) 링크를 공유할 수 있다.
 */
(function () {
  'use strict';

  var list = document.querySelector('[role="tablist"]');
  if (!list) return;

  var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
  if (!tabs.length) return;

  var panels = tabs.map(function (t) {
    return document.getElementById(t.getAttribute('aria-controls'));
  }).filter(Boolean);
  if (panels.length !== tabs.length) return;

  function select(index, focus) {
    tabs.forEach(function (tab, i) {
      var on = i === index;
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      // 선택된 탭만 Tab 키 순서에 남긴다 (좌우 화살표로 이동하는 게 표준 동작)
      tab.setAttribute('tabindex', on ? '0' : '-1');
      panels[i].hidden = !on;
    });
    if (focus) tabs[index].focus();

    var id = tabs[index].id.replace(/^tab-/, '');
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', '#' + id);
    }
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { select(i); });
    tab.addEventListener('keydown', function (e) {
      var next = null;
      if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      if (next !== null) {
        e.preventDefault();
        select(next, true);
      }
    });
  });

  // 주소의 #해시로 시작 탭 결정
  var start = 0;
  var hash = (window.location.hash || '').replace(/^#/, '');
  if (hash) {
    tabs.forEach(function (t, i) {
      if (t.id === 'tab-' + hash) start = i;
    });
  }
  select(start);
})();
