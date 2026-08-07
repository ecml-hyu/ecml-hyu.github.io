/*
 * 뉴스룸 '새 게시물' 버튼.
 *
 * 정적 사이트라 글을 서버에 저장할 수 없다. 대신 GitHub 의 '새 파일 작성' 화면을
 * 오늘 날짜 파일명 + 본문 템플릿이 미리 채워진 상태로 열어준다.
 * 작성자가 Commit 을 누르면 GitHub 이 빌드해서 사이트에 반영한다.
 *
 * HTML 에도 링크가 들어있어(빌드 시각 기준) JS 가 꺼져 있어도 동작한다.
 * 이 스크립트는 날짜를 '오늘'로 고쳐주고 템플릿을 붙이는 역할만 한다.
 */
(function () {
  'use strict';

  var btn = document.getElementById('new-post-btn');
  var upload = document.getElementById('upload-media-btn');
  if (!btn) return;

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  var now = new Date();
  var today = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate());

  // _posts 파일명과 이미지 폴더에 같은 slug 를 쓴다.
  var slug = 'new-post';
  var imgDir = 'assets/img/news/' + today + '-' + slug;

  var template = [
    '---',
    'title: "제목을 입력하세요"',
    'date: ' + today,
    'description: "목록에 보일 한두 줄 요약."',
    '',
    '# 사진을 올렸다면 아래 줄들의 맨 앞 "# " 를 지우세요.',
    '# 지우지 않으면 사진 없는 글로 정상 게시됩니다.',
    '#',
    '# 대표이미지 — 목록에 썸네일로 보입니다.',
    '# thumbnail: /' + imgDir + '/cover.webp',
    '#',
    '# 본문 아래 갤러리에 순서대로 표시됩니다. 장수만큼 줄을 늘리세요.',
    '# images:',
    '#   - /' + imgDir + '/1.webp',
    '#   - /' + imgDir + '/2.webp',
    '---',
    '',
    '여기에 본문을 씁니다. 빈 줄로 문단을 나눕니다.',
    '',
    '## 소제목',
    '',
    '- 목록도 쓸 수 있습니다',
    '- [링크](https://example.com) 도 됩니다',
    '',
    '> 사진은 먼저 "사진 업로드" 버튼으로',
    '> ' + imgDir + '/ 에 올린 뒤 위 경로를 맞춰 주세요.',
    ''
  ].join('\n');

  var base = 'https://github.com/' + btn.getAttribute('data-repo') +
             '/new/' + btn.getAttribute('data-branch');
  btn.href = base +
    '?filename=_posts/' + today + '-' + slug + '.md' +
    '&value=' + encodeURIComponent(template);

  if (upload) {
    upload.href = 'https://github.com/' + upload.getAttribute('data-repo') +
                  '/upload/' + upload.getAttribute('data-branch') +
                  '/' + imgDir;
  }
})();
