# -*- coding: utf-8 -*-
"""_data/publications.yml 의 DOI 를 CrossRef 와 대조한다.

자동으로 고치지 않는다. 차이가 나면 양쪽 값을 scripts/mismatch.log 에 적고
사람이 판단하도록 남긴다.

저널명은 원본이 약어("Water Res."), CrossRef 가 정식명("Water Research") 이라
단순 비교하면 전부 불일치로 잡힌다. 약어-정식명 대응을 따로 판정한다.

사용법:
    python scripts/verify_doi.py
    CROSSREF_MAILTO=you@example.com python scripts/verify_doi.py
"""
import io
import os
import html as htmllib
import re
import sys
import time
import json
import datetime
import requests
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MISMATCH = os.path.join(HERE, "mismatch.log")

DELAY = 0.5          # CrossRef rate limit 배려
TIMEOUT = 30

# CrossRef 는 연락처가 있으면 polite pool 로 처리한다.
MAILTO = os.environ.get("CROSSREF_MAILTO", "ecml@hanyang.ac.kr")
UA = {"User-Agent": "ECML-site-migration/1.0 (https://ecml.hanyang.ac.kr; mailto:%s)" % MAILTO}

STOP = {"of", "the", "and", "for", "in", "on", "a", "an", "&"}


def norm_title(s):
    if not s:
        return ""
    s = htmllib.unescape(s)                           # &amp; &lt; 등을 먼저 푼다
    s = re.sub(r"<[^>]+>", " ", s)                    # CrossRef 제목에 태그가 섞여 온다
    s = s.replace("−", "-").replace("–", "-").replace("—", "-").replace("‐", "-")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    s = htmllib.unescape(s or "").lower().replace(".", " ")
    return [t for t in re.split(r"[^a-z0-9]+", s) if t and t not in STOP]


def journal_matches(ours, theirs):
    """'Water Res.' 와 'Water Research' 를 같은 것으로 본다."""
    a, b = tokens(ours), tokens(theirs)
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) != len(b):
        return False
    return all(y.startswith(x) for x, y in zip(a, b))


CACHE = os.path.join(HERE, "raw", "crossref")


def crossref(doi):
    """응답을 scripts/raw/crossref/ 에 캐시한다. 재실행이 API 를 다시 때리지 않도록."""
    if not os.path.isdir(CACHE):
        os.makedirs(CACHE)
    key = re.sub(r"[^A-Za-z0-9._-]", "_", doi) + ".json"
    cached = os.path.join(CACHE, key)
    if os.path.exists(cached):
        blob = json.load(io.open(cached, encoding="utf-8"))
        return blob.get("message"), blob.get("error")

    url = "https://api.crossref.org/works/" + requests.utils.quote(doi, safe="")
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    if r.status_code == 404:
        json.dump({"message": None, "error": "DOI를 CrossRef에서 찾을 수 없음 (404)"},
                  io.open(cached, "w", encoding="utf-8"), ensure_ascii=False)
        return None, "DOI를 CrossRef에서 찾을 수 없음 (404)"
    if r.status_code == 200:
        try:
            msg = r.json()["message"]
            json.dump({"message": msg, "error": None},
                      io.open(cached, "w", encoding="utf-8"), ensure_ascii=False)
            return msg, None
        except Exception as exc:
            return None, "응답 파싱 실패: %s" % exc
    return None, "HTTP %s" % r.status_code



def cache_hit(doi):
    if not doi:
        return True
    key = re.sub(r"[^A-Za-z0-9._-]", "_", doi) + ".json"
    return os.path.exists(os.path.join(CACHE, key))


def cr_year(msg):
    for key in ("published-print", "published-online", "published", "issued", "created"):
        node = msg.get(key) or {}
        parts = node.get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def main():
    pubs = yaml.safe_load(io.open(os.path.join(ROOT, "_data", "publications.yml"),
                                  encoding="utf-8").read())
    lines = []
    stats = {"checked": 0, "ok": 0, "mismatch": 0, "no_doi": 0, "api_error": 0}
    mismatched_ids = []

    for p in pubs:
        tag = "%s #%s" % (p["type"], p["id"])
        doi = p.get("doi")
        if not doi:
            stats["no_doi"] += 1
            lines.append("[DOI 없음]     %s | %s" % (tag, p["title"][:70]))
            continue

        stats["checked"] += 1
        try:
            msg, err = crossref(doi)
        except Exception as exc:
            msg, err = None, "요청 실패: %s" % exc

        if msg is None:
            stats["api_error"] += 1
            lines.append("[조회 실패]    %s | doi=%s | %s" % (tag, doi, err))
            if not cache_hit(doi):
                time.sleep(DELAY)
            continue

        diffs = []

        their_title = (msg.get("title") or [""])[0]
        if norm_title(their_title) != norm_title(p["title"]):
            diffs.append(("제목", p["title"], their_title))

        their_journal = (msg.get("container-title") or [""])[0]
        if p.get("journal") and their_journal and not journal_matches(p["journal"], their_journal):
            diffs.append(("저널", p["journal"], their_journal))

        ty = cr_year(msg)
        if p.get("year") and ty and int(p["year"]) != ty:
            diffs.append(("연도", p["year"], ty))
        if not p.get("year") and ty:
            diffs.append(("연도(원본 없음)", None, ty))

        if diffs:
            stats["mismatch"] += 1
            mismatched_ids.append(tag)
            lines.append("[불일치]       %s | doi=%s" % (tag, doi))
            for field, ours, theirs in diffs:
                lines.append("    %s" % field)
                lines.append("        원본    : %s" % ours)
                lines.append("        CrossRef: %s" % theirs)
        else:
            stats["ok"] += 1

        if not cache_hit(p.get('doi')):
            time.sleep(DELAY)

    header = [
        "=== verify_doi.py @ %s ===" % datetime.datetime.now().isoformat(timespec="seconds"),
        "대조 %d건 / 일치 %d / 불일치 %d / 조회실패 %d / DOI없음 %d"
        % (stats["checked"], stats["ok"], stats["mismatch"], stats["api_error"], stats["no_doi"]),
        "※ 자동 수정하지 않았다. 아래 항목은 사람이 확인해야 한다.",
        "",
    ]
    with io.open(MISMATCH, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(header + (lines or ["  (확인할 항목 없음)"])) + "\n")

    print("대조 %d건" % stats["checked"])
    print("  일치      %d" % stats["ok"])
    print("  불일치    %d" % stats["mismatch"])
    print("  조회실패  %d" % stats["api_error"])
    print("  DOI없음   %d" % stats["no_doi"])
    if mismatched_ids:
        print("\n  확인 필요: %s" % ", ".join(mismatched_ids))
    print("\n  -> scripts/mismatch.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
