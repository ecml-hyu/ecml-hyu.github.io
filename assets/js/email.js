/*
 * 이메일 주소 조합.
 *
 * _data/members.yml 에는 user 와 domain 이 따로 저장돼 있고, HTML 소스에도
 * 그렇게 나간다. 완성된 주소는 이 스크립트가 만든다. 페이지 소스를 긁어가는
 * 스팸 봇이 주소를 그대로 가져가지 못하게 하려는 것이다.
 *
 * JS 가 꺼져 있으면 링크가 동작하지 않는다. 그 경우를 위해 클릭 시
 * 주소를 화면에 보여 주기만 한다.
 */
(function () {
  'use strict';

  var links = document.querySelectorAll('.email-link');
  if (!links.length) return;

  Array.prototype.forEach.call(links, function (el) {
    var user = el.getAttribute('data-user');
    var domain = el.getAttribute('data-domain');
    if (!user || !domain) return;

    var address = user + '@' + domain;
    el.setAttribute('href', 'mailto:' + address);
    el.setAttribute('title', address);

    // 링크를 눌러 메일 앱이 열리지 않는 환경에서도 주소를 확인할 수 있게
    // 두 번째 클릭에서는 주소를 그대로 노출한다.
    el.addEventListener('click', function () {
      if (el.dataset.revealed) return;
      el.dataset.revealed = '1';
      el.textContent = address;
    });
  });
})();
