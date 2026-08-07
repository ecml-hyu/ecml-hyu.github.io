# -*- coding: utf-8 -*-
"""구 홈페이지(Google Sites)의 원본 HTML을 scripts/raw/ 에 저장한다.

파싱보다 먼저 원본을 확보해 두는 것이 목적이다. 구 사이트가 내려가도
raw/ 만 있으면 파싱을 다시 할 수 있다.

사용법:
    python scripts/fetch_pages.py            # 없는 것만 받음
    python scripts/fetch_pages.py --force    # 전부 다시 받음
"""
import os
import sys
import time
import json
import datetime
import requests

BASE = "https://sites.google.com/view/encpl"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

# 서버에 부담을 주지 않기 위한 요청 간격(초)
DELAY = 1.0

UA = {
    "User-Agent": "Mozilla/5.0 (compatible; ECML-site-migration/1.0; "
                  "+https://ecml.hanyang.ac.kr)"
}

PAGES = [
    ("people-principle-investigator", "/people/principle-investigator"),
    ("people-graduates",              "/people/graduates"),
    ("people-undergraduates",         "/people/undergraduates"),
    ("people-alumni",                 "/people/alumni"),
    ("publications-scie",             "/publications/peer-reviewed-journal-papers-scie"),
    ("publications-domestic",         "/publications/peer-reviewed-journal-papers-domestic"),
    ("publications-book-chapters",    "/publications/book-chapters"),
    ("publications-books",            "/publications/books"),
    ("patents",                       "/patents"),
    ("projects",                      "/projects"),
    ("news",                          "/news"),
    ("research",                      "/research"),
    ("index",                         "/"),
]


def main():
    force = "--force" in sys.argv
    if not os.path.isdir(RAW):
        os.makedirs(RAW)

    manifest = []
    failures = []

    for i, (slug, path) in enumerate(PAGES):
        dest = os.path.join(RAW, slug + ".html")
        if os.path.exists(dest) and not force:
            print("  skip     %-32s (이미 있음)" % slug)
            manifest.append({"slug": slug, "path": path, "status": "cached",
                             "bytes": os.path.getsize(dest)})
            continue

        url = BASE + path
        try:
            r = requests.get(url, headers=UA, timeout=45)
            status = r.status_code
            if status != 200:
                raise RuntimeError("HTTP %s" % status)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(r.text)
            print("  ok       %-32s %7d bytes" % (slug, len(r.text)))
            manifest.append({"slug": slug, "path": path, "url": url,
                             "status": status, "bytes": len(r.text)})
        except Exception as exc:
            print("  FAILED   %-32s %s" % (slug, exc))
            failures.append({"slug": slug, "url": url, "error": str(exc)})

        # 마지막 요청 뒤에는 기다리지 않는다
        if i < len(PAGES) - 1:
            time.sleep(DELAY)

    meta = {
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "base": BASE,
        "delay_seconds": DELAY,
        "pages": manifest,
        "failures": failures,
    }
    with open(os.path.join(RAW, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\n  받은 페이지 %d개, 실패 %d개" % (len(manifest), len(failures)))
    if failures:
        for x in failures:
            print("    - %s : %s" % (x["slug"], x["error"]))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
