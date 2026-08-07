# -*- coding: utf-8 -*-
"""배포 전 점검. push 하기 전에 한 번 돌리면 흔한 사고를 미리 잡는다.

    python scripts/check_site.py

지금까지 실제로 라이브를 깨뜨렸던 것들을 검사한다.
  - _config.yml 의 필수 키 누락 (편집 실수로 통째로 날아간 적 있음)
  - {% feed_meta %} 를 쓰면서 jekyll-feed 를 안 켠 경우 -> 빌드 실패
  - 최상위 permalink (페이지 URL 까지 바뀌어 전부 404 가 된 적 있음)
  - 밑줄로 시작하는 assets 파일 (Jekyll 이 빌드에서 제외 -> 404)
  - members.yml 의 photo 가 실제로 없는 파일을 가리키는 경우
  - Liquid 블록 짝 안 맞음
  - 커밋되면 안 되는 문서 파일이 저장소에 들어온 경우
"""
import io
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)

errors, warns, oks = [], [], []


def read(p):
    return io.open(p, encoding="utf-8").read()


# ---------- _config.yml ----------
try:
    import yaml
    cfg = yaml.safe_load(read("_config.yml"))
except Exception as exc:
    print("_config.yml 파싱 실패: %s" % exc)
    sys.exit(1)

REQUIRED = ["title", "url", "baseurl", "lang", "plugins", "defaults",
            "exclude", "repository", "branch", "og_image"]
for k in REQUIRED:
    if k not in cfg:
        errors.append("_config.yml 에 '%s' 키가 없다" % k)
    else:
        oks.append("config.%s" % k)

if cfg.get("url") != "https://ecml.hanyang.ac.kr":
    errors.append("_config.yml url 이 %r 이다" % cfg.get("url"))
if cfg.get("baseurl") not in ("", None):
    errors.append("_config.yml baseurl 이 %r 이다 (빈 문자열이어야 함)" % cfg.get("baseurl"))

# 최상위 permalink 는 페이지 URL 까지 바꾼다
if "permalink" in cfg:
    errors.append("_config.yml 최상위에 permalink 가 있다. "
                  "페이지 주소가 전부 바뀌어 404 가 된다. defaults 의 type: posts 안으로 옮길 것")
else:
    oks.append("최상위 permalink 없음")

# ---------- 플러그인 태그 ----------
plugins = cfg.get("plugins") or []
ALLOWED = {"jekyll-feed", "jekyll-seo-tag", "jekyll-sitemap"}
bad = [p for p in plugins if p not in ALLOWED]
if bad:
    errors.append("GitHub Pages 화이트리스트 밖 플러그인: %s" % bad)

TAG_NEEDS = {"feed_meta": "jekyll-feed", "seo": "jekyll-seo-tag"}
for path in glob.glob("_includes/*.html") + glob.glob("_layouts/*.html") + glob.glob("*.html"):
    text = read(path)
    for tag, need in TAG_NEEDS.items():
        if re.search(r"\{%-?\s*" + tag + r"\s*-?%\}", text) and need not in plugins:
            errors.append("%s 가 {%% %s %%} 를 쓰는데 _config.yml plugins 에 %s 가 없다 "
                          "(Unknown tag 로 빌드 실패한다)" % (path, tag, need))
if not any("Unknown tag" in e for e in errors):
    oks.append("플러그인 태그와 plugins 목록 일치")

# ---------- 밑줄로 시작하는 assets ----------
under = [p for p in glob.glob("assets/**/*", recursive=True)
         if os.path.isfile(p) and os.path.basename(p).startswith("_")]
if under:
    errors.append("assets 안에 밑줄로 시작하는 파일이 있다 (Jekyll 이 빌드에서 제외해 404): %s" % under)
else:
    oks.append("assets 에 밑줄 파일 없음")

# ---------- members 사진 경로 ----------
if os.path.exists("_data/members.yml"):
    for m in (yaml.safe_load(read("_data/members.yml")) or []):
        p = m.get("photo")
        if p and not os.path.exists(p.lstrip("/")):
            errors.append("members.yml: %s 의 photo 가 없는 파일을 가리킨다 (%s)"
                          % (m.get("name_en"), p))
    if not any("photo 가 없는" in e for e in errors):
        oks.append("members 사진 경로 모두 실재")

# ---------- Liquid 블록 ----------
BLOCKS = {"if": "endif", "unless": "endunless", "for": "endfor",
          "case": "endcase", "capture": "endcapture", "comment": "endcomment", "raw": "endraw"}
ENDS = set(BLOCKS.values())
for path in glob.glob("*.html") + glob.glob("_layouts/*.html") + glob.glob("_includes/*.html"):
    stack = []
    for m in re.finditer(r"\{%-?\s*(\w+)", read(path)):
        t = m.group(1)
        if t in BLOCKS:
            stack.append(t)
        elif t in ENDS:
            if not stack or BLOCKS[stack.pop()] != t:
                errors.append("%s: Liquid 블록 짝이 맞지 않는다 (%s)" % (path, t))
                break
    if stack:
        errors.append("%s: 닫히지 않은 Liquid 블록 %s" % (path, stack))
if not any("Liquid" in e for e in errors):
    oks.append("Liquid 블록 짝 정상")

# ---------- 배포되면 안 되는 파일 ----------
JUNK = (".pptx", ".docx", ".xlsx", ".hwp", ".zip", ".psd", ".ai")
found = [p for p in os.listdir(".") if os.path.splitext(p)[1].lower() in JUNK]
if found:
    warns.append("작업용 문서가 저장소 루트에 있다 (.gitignore 확인): %s" % found)

# ---------- CNAME ----------
if os.path.exists("CNAME"):
    raw = open("CNAME", "rb").read()
    if raw.strip() != b"ecml.hanyang.ac.kr":
        errors.append("CNAME 내용이 바뀌었다: %r" % raw)
    else:
        oks.append("CNAME 정상")
else:
    errors.append("CNAME 이 없다. 도메인 연결이 끊긴다")

# ---------- 결과 ----------
print("통과 %d개" % len(oks))
for w in warns:
    print("  경고  %s" % w)
print()
if errors:
    print("문제 %d건" % len(errors))
    for e in errors:
        print("  X  %s" % e)
    print("\npush 하기 전에 고칠 것.")
    sys.exit(1)
print("문제 없음. 배포해도 된다.")
sys.exit(0)
