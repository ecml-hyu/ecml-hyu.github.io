/*
 * 인트로 애니메이션 — 세션당 1회만 재생.
 *
 * <head> 에서 동기적으로 로드된다. 그 시점에 <body> 는 아직 파싱되지 않았으므로
 * 1단계에서는 documentElement 에만 클래스를 붙인다. 그래야 첫 페인트 전에
 * `html.intro-seen .intro{display:none}` 이 적용되어 깜빡임이 생기지 않는다.
 *
 * 타이밍(3150ms)과 skip 버튼 동작은 sindoll2 님 원본과 동일하다.
 */
(function () {
  'use strict';

  var KEY = 'ecml-intro-seen';
  var seen = false;

  // 프라이빗 모드 등 sessionStorage 가 막힌 환경에서도 페이지는 정상 동작해야 한다.
  try {
    seen = window.sessionStorage.getItem(KEY) === '1';
  } catch (e) {
    seen = false;
  }

  if (seen) {
    document.documentElement.classList.add('intro-seen');
    return;
  }

  try {
    window.sessionStorage.setItem(KEY, '1');
  } catch (e) {
    /* 저장 실패는 무시 — 다음 로드에서 한 번 더 재생될 뿐이다 */
  }

  document.addEventListener('DOMContentLoaded', function () {
    var intro = document.getElementById('intro');
    if (!intro) return;

    var open = function () { intro.classList.add('open'); };
    setTimeout(open, 3150);

    var skip = document.getElementById('skip');
    if (skip) skip.onclick = open;
  });
})();
