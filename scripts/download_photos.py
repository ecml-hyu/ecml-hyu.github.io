# -*- coding: utf-8 -*-
"""구성원 사진을 로컬로 내려받아 정사각형 WebP 로 변환한다.

구 사이트(lh3.googleusercontent.com)가 사라져도 새 사이트가 깨지지 않도록
원본을 저장소 안으로 가져오는 것이 목적이다.

    원본  -> assets/img/members/_original/{slug}.{ext}
    결과  -> assets/img/members/{slug}.webp   (600x600, q85)

얼굴 중심 크롭:
  OpenCV 얼굴 캐스케이드를 쓸 수 있으면 얼굴 중심으로 자른다.
  없으면 인물 사진 관례에 맞춰 위쪽에 치우친 크롭을 쓴다(--bias 로 조절).
  어느 쪽을 썼는지 항상 출력한다.

사용법:
    python scripts/download_photos.py
    python scripts/download_photos.py --force
"""
import io
import os
import sys
import json
import time
import datetime
import requests
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")
MANIFEST = os.path.join(RAW, "photo_manifest.json")
OUT_DIR = os.path.join(ROOT, "assets", "img", "members")
ORIG_DIR = os.path.join(OUT_DIR, "_original")
FAILED = os.path.join(HERE, "failed.log")

DELAY = 1.0
SIZE = 600
QUALITY = 85
# 얼굴 검출을 못 할 때 세로 크롭 위치. 0.0=위끝, 0.5=정중앙.
# 인물 사진은 얼굴이 위쪽에 있으므로 0.5보다 작게 잡는다.
VERTICAL_BIAS = 0.38

UA = {"User-Agent": "Mozilla/5.0 (compatible; ECML-site-migration/1.0; "
                    "+https://ecml.hanyang.ac.kr)"}

failures = []


def load_detector():
    """가능하면 OpenCV 얼굴 검출기를 준비한다. 없으면 None."""
    try:
        import cv2
    except ImportError:
        return None
    for path in (
        os.path.join(getattr(cv2, "data", type("x", (), {"haarcascades": ""})).haarcascades,
                     "haarcascade_frontalface_default.xml"),
        os.path.join(os.path.dirname(cv2.__file__), "data",
                     "haarcascade_frontalface_default.xml"),
    ):
        if path and os.path.exists(path):
            clf = cv2.CascadeClassifier(path)
            if not clf.empty():
                return (cv2, clf)
    return None


def face_center(detector, path):
    """(cx, cy) 를 0~1 비율로 돌려준다. 실패하면 None."""
    if detector is None:
        return None
    cv2, clf = detector
    img = cv2.imread(path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = clf.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    H, W = gray.shape[:2]
    return ((x + w / 2.0) / W, (y + h / 2.0) / H)


def square_crop(im, center=None):
    """짧은 변 기준 정사각형 크롭. center 가 있으면 그 지점을 중심으로."""
    w, h = im.size
    side = min(w, h)
    if center:
        cx, cy = center[0] * w, center[1] * h
    else:
        cx, cy = w / 2.0, h * VERTICAL_BIAS
    left = int(round(cx - side / 2.0))
    top = int(round(cy - side / 2.0))
    left = max(0, min(left, w - side))
    top = max(0, min(top, h - side))
    return im.crop((left, top, left + side, top + side))


def main():
    force = "--force" in sys.argv
    if not os.path.exists(MANIFEST):
        print("photo_manifest.json 이 없다. 먼저 parse_members.py 를 실행할 것.")
        return 1
    manifest = json.load(io.open(MANIFEST, encoding="utf-8"))

    for d in (OUT_DIR, ORIG_DIR):
        if not os.path.isdir(d):
            os.makedirs(d)

    detector = load_detector()
    print("얼굴 검출: %s\n" % ("OpenCV 캐스케이드 사용"
                              if detector else "사용 불가 -> 위쪽 치우친 크롭(bias=%.2f)" % VERTICAL_BIAS))

    rows = []
    total_before = total_after = 0
    items = sorted(manifest.items())

    for i, (slug, info) in enumerate(items):
        src = info["source"]
        orig_path = None
        try:
            existing = [f for f in os.listdir(ORIG_DIR) if f.startswith(slug + ".")]
            if existing and not force:
                orig_path = os.path.join(ORIG_DIR, existing[0])
            else:
                r = requests.get(src, headers=UA, timeout=60)
                if r.status_code != 200:
                    raise RuntimeError("HTTP %s" % r.status_code)
                ctype = (r.headers.get("Content-Type") or "").lower()
                ext = "png" if "png" in ctype else ("webp" if "webp" in ctype else "jpg")
                orig_path = os.path.join(ORIG_DIR, "%s.%s" % (slug, ext))
                with open(orig_path, "wb") as f:
                    f.write(r.content)
                if i < len(items) - 1:
                    time.sleep(DELAY)

            before = os.path.getsize(orig_path)
            im = Image.open(orig_path)
            src_size = im.size
            im = im.convert("RGB")

            ctr = face_center(detector, orig_path)
            im2 = square_crop(im, ctr)
            im2 = im2.resize((SIZE, SIZE), Image.LANCZOS)
            dest = os.path.join(OUT_DIR, slug + ".webp")
            im2.save(dest, "WEBP", quality=QUALITY, method=6)
            after = os.path.getsize(dest)

            total_before += before
            total_after += after
            rows.append((slug, src_size, before, after, "face" if ctr else "bias"))
            print("  ok   %-16s %-11s %7.1fKB -> %6.1fKB  (%s)"
                  % (slug, "%dx%d" % src_size, before / 1024.0, after / 1024.0,
                     "얼굴중심" if ctr else "위쪽크롭"))
        except Exception as exc:
            failures.append("사진 %s : %s (%s)" % (slug, exc, src[:80]))
            print("  FAIL %-16s %s" % (slug, exc))

    with io.open(FAILED, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n=== download_photos.py @ %s ===\n"
                % datetime.datetime.now().isoformat(timespec="seconds"))
        f.write("".join("  %s\n" % x for x in failures) if failures else "  (실패 항목 없음)\n")

    print("\n  성공 %d / 실패 %d" % (len(rows), len(failures)))
    print("  원본 합계 %.1f KB -> 변환 합계 %.1f KB (%.1f%% 감소)"
          % (total_before / 1024.0, total_after / 1024.0,
             (1 - total_after / float(total_before)) * 100 if total_before else 0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
