# -*- coding: utf-8 -*-
"""구성원 사진을 넣는다. 폴더에 사진을 모아두고 한 번 실행하면 끝난다.

하는 일
  1) 사진을 정사각형 600x600 WebP 로 변환해 assets/img/members/ 에 저장
  2) _data/members.yml 의 photo 항목을 그 경로로 자동 갱신

사용법
    python scripts/add_member_photos.py <사진들이 있는 폴더>
    python scripts/add_member_photos.py <폴더> --dry-run     # 뭐가 바뀌는지만 보기

파일 이름 맞추는 법
  파일 이름에 아래 중 아무거나 들어있으면 그 사람으로 인식한다.
    - photo_slug        예) kiho-park.jpg
    - 영문 이름         예) Kiho Park.jpg,  KihoPark.png
    - 한글 이름         예) 박기호.jpg
  못 찾은 파일은 건너뛰고 목록으로 알려준다.

이미 있는 사진을 덮어쓰려면 --overwrite 를 준다.
"""
import io
import os
import re
import sys
import argparse
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "assets", "img", "members")
YML = os.path.join(ROOT, "_data", "members.yml")

SIZE = 600
QUALITY = 85
# 얼굴이 위쪽에 있는 인물 사진 기준. 0.5 면 정중앙.
VERTICAL = 0.40
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif")


def norm_key(s):
    return re.sub(r"[^a-z0-9가-힣]", "", (s or "").lower())


def load_members():
    """YAML 파서를 쓰지 않는다. 주석과 서식을 보존한 채 photo 줄만 고쳐야 하기 때문."""
    text = io.open(YML, encoding="utf-8").read()
    blocks = []
    for m in re.finditer(r"(?m)^- name_en: \"([^\"]+)\"(.*?)(?=^- name_en: |\Z)", text, re.S):
        body = m.group(0)
        name_en = m.group(1)
        ko = re.search(r'^\s*name_ko: "([^"]*)"', body, re.M)
        slug = re.search(r'^\s*photo_slug: "([^"]*)"', body, re.M)
        blocks.append({
            "name_en": name_en,
            "name_ko": ko.group(1) if ko else "",
            "slug": slug.group(1) if slug else "",
            "start": m.start(), "end": m.end(),
        })
    return text, blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="사진들이 들어있는 폴더")
    ap.add_argument("--dry-run", action="store_true", help="바뀌는 내용만 출력")
    ap.add_argument("--overwrite", action="store_true", help="이미 있는 사진도 덮어쓴다")
    args = ap.parse_args()

    if not os.path.isdir(args.src):
        print("폴더를 찾을 수 없다: %s" % args.src)
        return 1
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    text, members = load_members()
    if not members:
        print("_data/members.yml 에서 구성원을 읽지 못했다.")
        return 1

    files = [f for f in sorted(os.listdir(args.src))
             if os.path.splitext(f)[1].lower() in EXTS]
    if not files:
        print("이미지가 없다: %s" % args.src)
        return 1

    matched, skipped, done = [], [], []
    default_src = None

    for f in files:
        stem = os.path.splitext(f)[0]
        if norm_key(stem) in ("기본이미지", "default", "defaultavatar", "기본"):
            default_src = f          # 사람이 아니라 기본 아바타용 그림
            continue
        key = norm_key(os.path.splitext(f)[0])
        hit = None
        for m in members:
            for cand in (m["slug"], m["name_en"], m["name_ko"]):
                if cand and norm_key(cand) and norm_key(cand) in key:
                    hit = m
                    break
            if hit:
                break
        if hit:
            matched.append((f, hit))
        else:
            skipped.append(f)

    for f, m in matched:
        dest = os.path.join(OUT_DIR, m["slug"] + ".webp")
        if os.path.exists(dest) and not args.overwrite:
            print("  건너뜀  %-22s 이미 있음 (--overwrite 로 덮어쓰기)" % (m["slug"] + ".webp"))
            continue
        src = os.path.join(args.src, f)
        before = os.path.getsize(src)
        if not args.dry_run:
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im = ImageOps.fit(im, (SIZE, SIZE), Image.LANCZOS, centering=(0.5, VERTICAL))
            im.save(dest, "WEBP", quality=QUALITY, method=6)
            after = os.path.getsize(dest)
        else:
            after = 0
        done.append(m)
        print("  변환    %-22s <- %-28s %6.1fKB -> %6.1fKB"
              % (m["slug"] + ".webp", f, before / 1024.0, after / 1024.0))

    # 기본 아바타 갱신 (사진 없는 사람에게 쓰이는 그림)
    if default_src:
        dest = os.path.join(OUT_DIR, "default-avatar.webp")
        src = os.path.join(args.src, default_src)
        before = os.path.getsize(src)
        if not args.dry_run:
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im = ImageOps.fit(im, (SIZE, SIZE), Image.LANCZOS, centering=(0.5, 0.5))
            im.save(dest, "WEBP", quality=QUALITY, method=6)
            after = os.path.getsize(dest)
        else:
            after = 0
        print("  기본이미지 default-avatar.webp   <- %-22s %6.1fKB -> %6.1fKB"
              % (default_src, before / 1024.0, after / 1024.0))
        print("           _config.yml 의 default_member_photo 를")
        print("           /assets/img/members/default-avatar.webp 로 맞춰 두세요.")

    # members.yml 의 photo 줄 갱신 (뒤에서부터 바꿔야 위치가 안 밀린다)
    changed = 0
    for m in sorted(members, key=lambda x: -x["start"]):
        path = os.path.join(OUT_DIR, m["slug"] + ".webp")
        want = ('"/assets/img/members/%s.webp"' % m["slug"]) if os.path.exists(path) else "null"
        block = text[m["start"]:m["end"]]
        new_block, n = re.subn(r"(?m)^(\s*photo:\s*).*$", lambda mo: mo.group(1) + want, block)
        if n and new_block != block:
            text = text[:m["start"]] + new_block + text[m["end"]:]
            changed += 1

    if args.dry_run:
        print("\n[dry-run] 파일도 YAML 도 건드리지 않았다.")
    elif changed:
        io.open(YML, "w", encoding="utf-8", newline="\n").write(text)
        print("\n  _data/members.yml 의 photo 항목 %d개 갱신" % changed)
    else:
        print("\n  members.yml 은 이미 최신이다.")

    if skipped:
        print("\n  이름을 못 맞춘 파일 %d개:" % len(skipped))
        for f in skipped:
            print("    - %s" % f)
        print("  파일 이름에 photo_slug / 영문이름 / 한글이름 중 하나를 넣어 주세요.")
        print("  쓸 수 있는 slug: %s" % ", ".join(m["slug"] for m in members))

    print("\n  처리 %d명 / 미매칭 %d개" % (len(done), len(skipped)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
