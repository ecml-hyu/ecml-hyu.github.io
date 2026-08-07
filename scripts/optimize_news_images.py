# -*- coding: utf-8 -*-
"""뉴스 글에 넣을 사진을 WebP 로 줄이고, 글에 붙여넣을 front matter 를 만들어 준다.

GitHub 웹에서 사진을 올리면 원본 그대로 저장된다. 요즘 휴대폰 사진은 한 장에
3~5MB 라 그대로 두면 페이지가 느려진다. 이 스크립트로 한 번 줄여서 올리면 된다.

사용법:
    python scripts/optimize_news_images.py <사진들이 있는 폴더> [--slug 2026-08-07-workshop]

    # 예: 바탕화면 사진 폴더를 정리해서 assets/img/news/2026-08-07-workshop/ 로
    python scripts/optimize_news_images.py "C:/Users/USER/Desktop/사진들" --slug 2026-08-07-workshop

cover.webp 로 쓸 사진은 --cover 로 지정한다. 없으면 첫 번째 사진을 쓴다.
"""
import io
import os
import re
import sys
import argparse
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

MAX_WIDTH = 1600          # 본문 갤러리용 최대 가로폭
COVER_SIZE = (880, 600)   # 대표이미지(목록 썸네일)
QUALITY = 82
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tif", ".tiff")


def human(n):
    return "%.1f KB" % (n / 1024.0) if n < 1024 * 1024 else "%.1f MB" % (n / 1048576.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="원본 사진이 있는 폴더")
    ap.add_argument("--slug", help="assets/img/news/<slug>/ 로 저장. 기본값은 폴더 이름")
    ap.add_argument("--cover", help="대표이미지로 쓸 파일 이름")
    args = ap.parse_args()

    if not os.path.isdir(args.src):
        print("폴더를 찾을 수 없다: %s" % args.src)
        return 1

    slug = args.slug or os.path.basename(os.path.normpath(args.src))
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", slug).strip("-").lower()
    out_dir = os.path.join(ROOT, "assets", "img", "news", slug)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    files = sorted(f for f in os.listdir(args.src)
                   if os.path.splitext(f)[1].lower() in EXTS)
    if not files:
        print("이미지가 없다: %s" % args.src)
        return 1

    cover_src = args.cover or files[0]
    if cover_src not in files:
        print("--cover 로 지정한 파일이 폴더에 없다: %s" % cover_src)
        return 1

    total_before = total_after = 0
    made = []

    def save(img, dest, size=None):
        im = Image.open(img)
        im = ImageOps.exif_transpose(im)      # 휴대폰 사진 회전 정보 반영
        im = im.convert("RGB")
        if size:
            im = ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.4))
        elif im.width > MAX_WIDTH:
            h = int(round(im.height * MAX_WIDTH / float(im.width)))
            im = im.resize((MAX_WIDTH, h), Image.LANCZOS)
        im.save(dest, "WEBP", quality=QUALITY, method=6)

    # 대표이미지
    src_cover = os.path.join(args.src, cover_src)
    dst_cover = os.path.join(out_dir, "cover.webp")
    b = os.path.getsize(src_cover)
    save(src_cover, dst_cover, COVER_SIZE)
    a = os.path.getsize(dst_cover)
    total_before += b
    total_after += a
    print("  cover.webp        %10s -> %10s   (%s)" % (human(b), human(a), cover_src))

    # 나머지 사진
    n = 0
    for f in files:
        n += 1
        src = os.path.join(args.src, f)
        dest = os.path.join(out_dir, "%d.webp" % n)
        b = os.path.getsize(src)
        save(src, dest)
        a = os.path.getsize(dest)
        total_before += b
        total_after += a
        made.append("/assets/img/news/%s/%d.webp" % (slug, n))
        print("  %-17s %10s -> %10s   (%s)" % ("%d.webp" % n, human(b), human(a), f))

    print("\n  합계 %s -> %s  (%.1f%% 감소)"
          % (human(total_before), human(total_after),
             (1 - total_after / float(total_before)) * 100 if total_before else 0))

    print("\n  글의 front matter 에 아래를 붙여넣으세요\n")
    print("thumbnail: /assets/img/news/%s/cover.webp" % slug)
    print("images:")
    for m in made:
        print("  - %s" % m)
    print("\n  그리고 %s\\ 안의 파일들을 GitHub 의" % out_dir)
    print("  assets/img/news/%s/ 에 업로드하면 됩니다." % slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
