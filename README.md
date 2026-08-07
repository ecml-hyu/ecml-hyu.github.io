# ecml-hyu.github.io

ECML research laboratory website — https://ecml.hanyang.ac.kr

디자인과 페이지 구성은 그대로이고, **헤더/푸터 중복만 Jekyll 레이아웃으로 합쳤습니다.**
화면에 보이는 결과물은 이전과 동일합니다.

---

## 무엇이 바뀌었나

전에는 7개 HTML 파일이 각자 똑같은 `<head>`, `<header>`, `<nav>`, `<footer>` 를
복사해서 갖고 있었습니다. 메뉴 하나 고치려면 7개 파일을 전부 고쳐야 했습니다.

이제는 공통 부분이 한 곳에만 있습니다.

```
_layouts/default.html    <html> ~ <head> ~ header ~ footer 껍데기 + 인트로 애니메이션
_layouts/page.html       하위 6개 페이지 공용 (page-head 배너 + 본문 영역)
_includes/head.html      <title>, meta, OG, favicon
_includes/nav.html       내비게이션 6개 항목  ← 메뉴 수정은 여기 한 곳만
_config.yml              사이트 제목, 주소 등
site.css                 스타일 (그대로, 위치도 그대로)
```

**주소는 하나도 안 바뀌었습니다.** `research.html` 은 여전히 `research.html` 입니다.

---

## 자주 하는 작업

### 페이지 내용 고치기

해당 파일(예: `research.html`)을 엽니다. 맨 위 `---` 사이는 설정이고,
그 아래가 본문입니다. **본문만 고치면 됩니다.**

```html
---
layout: page
title: "Research"              ← 배너의 큰 제목 + 브라우저 탭 제목
eyebrow: "WHAT WE STUDY"       ← 제목 위 작은 글씨
lead: "Modeling, optimization, ..."   ← 제목 아래 한 줄 설명
---
<div class="editable">...</div>       ← 여기부터가 본문
```

`title` / `eyebrow` / `lead` 를 고치면 배너가 바뀝니다.
`<header>` 나 `<footer>` 는 이제 이 파일에 없습니다 — 자동으로 붙습니다.

### 메뉴 추가·삭제·순서 변경

`_includes/nav.html` 의 이 줄 하나만 고칩니다. `파일명:표시이름` 형식입니다.

```
newsroom.html:Newsroom,members.html:Members,publications.html:Publications,research.html:Research,projects.html:Projects,contact.html:Contact
```

현재 보고 있는 페이지에 `.active` 클래스는 자동으로 붙습니다.

### 페이지 추가

기존 페이지 하나를 복사해서 이름만 바꾸고, 위 `---` 부분을 고친 뒤
`_includes/nav.html` 에 항목을 추가하면 끝입니다.

### 스타일 고치기

`site.css` 를 그대로 고치면 됩니다. 위치도 이름도 안 바뀌었습니다.

> ⚠️ **`site.css` 를 `.scss` 로 바꾸지 마세요.**
> Sass 는 `min()` 을 자기 내장 함수로 해석해서
> `width:min(1120px,calc(100% - 40px))` 에서 빌드를 실패시킵니다.
> 순수 CSS 로 두는 한 아무 문제 없습니다.

---

## 미리보기

**전과 달라진 점입니다.** 이제는 `index.html` 을 브라우저로 바로 열면
레이아웃이 적용되지 않아 본문 조각만 보입니다. Jekyll 을 거쳐야 합니다.

한 번만 설치하면 됩니다.

```bash
gem install bundler
bundle install
```

이후 미리보기 (파일을 저장하면 자동으로 다시 만들어집니다):

```bash
bundle exec jekyll serve
```

http://127.0.0.1:4000 에서 확인합니다.

빌드만 하려면:

```bash
bundle exec jekyll build      # 결과물이 _site/ 에 생성됨
```

`_site/` 는 빌드 결과라 git 에 올리지 않습니다 (`.gitignore` 처리됨).

---

## 건드리면 안 되는 것

- **`CNAME`** — 이 파일이 `ecml.hanyang.ac.kr` 도메인 연결을 유지합니다.
  지우거나 옮기거나 내용을 바꾸면 사이트가 도메인에서 내려갑니다.
- **`_config.yml` 의 `plugins`** — GitHub Pages 는 허용된 플러그인만 실행합니다.
  목록에 없는 플러그인을 추가하면 빌드가 조용히 실패합니다.

---

## 이미지

히어로 배경은 `assets/img/hero.webp` (30KB) 입니다.
원본 PNG 는 1.4MB 였고 `assets/img/hero-original.png` 에 보관돼 있습니다.
배경을 교체할 일이 있으면 WebP 로 변환해서 쓰는 편이 좋습니다 — 첫 화면이라
로딩 체감에 직접 영향을 줍니다.

---

## 배포

`main` 에 push 하면 GitHub Pages 가 자동으로 빌드·배포합니다 (보통 1~2분).
빌드가 실패하면 **이전 버전이 그대로 유지**되므로 사이트가 깨지지는 않습니다.
배포 상태는 저장소의 Deployments 탭에서 확인할 수 있습니다.
