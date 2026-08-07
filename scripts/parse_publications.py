# -*- coding: utf-8 -*-
"""scripts/raw/publications-*.html -> _data/publications.yml

핵심 아이디어: 제목은 항상 <a> 안에 있으므로 저자/제목 경계를 정규식이 아니라
DOM 으로 자른다. 저자 목록에 쉼표가 몇 개든 안전하다.

한 항목의 형태:
    (55) 저자목록, <a href="DOI">제목</a>, 저널 권(호) (연도) 페이지 (부가정보)

파싱하지 못한 항목은 버리지 않고 scripts/failed.log 에 남긴다.
"""
import io
import os
import re
import sys
import datetime
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")
FAILED = os.path.join(HERE, "failed.log")

SOURCES = [
    ("publications-scie",          "journal-scie"),
    ("publications-domestic",      "journal-domestic"),
    ("publications-book-chapters", "book-chapter"),
    ("publications-books",         "book"),
]

failures = []


def norm(s):
    """공백/특수문자 정규화. Google Sites 는 NBSP 와 유니코드 대시를 섞어 쓴다."""
    s = s.replace("\xa0", " ")
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def parse_authors(raw):
    """'A, B+, C*, and D*' -> [{name, corresponding, co_first}, ...]

    마커: * = 교신저자, + / 단검(dagger) = 공동 제1저자
    """
    raw = norm(raw).rstrip(",").strip()
    out = []
    for chunk in raw.split(","):
        name = chunk.strip()
        if not name:
            continue
        name = re.sub(r"^and\s+", "", name, flags=re.I).strip()
        if not name:
            continue
        corresponding = "*" in name
        co_first = ("+" in name) or ("†" in name)
        name = name.replace("*", "").replace("+", "").replace("†", "").strip()
        name = re.sub(r"\s+", " ", name)
        if not name:
            continue
        out.append({"name": name, "corresponding": corresponding, "co_first": co_first})
    return out


def parse_tail(tail):
    """', Water Res. 299 (2026) 125855 (IF: 12.4, Top 1.1% journal in ...)' 를 분해."""
    t = norm(tail)
    t = re.sub(r"^[,;]\s*", "", t)
    info = {"journal": None, "volume": None, "issue": None, "year": None,
            "pages": None, "impact_factor": None, "journal_rank": None,
            "publisher": None}

    # (IF: 12.4, Top 1.1% journal in Water Resources) / (IF: 4.7)
    m = re.search(r"\(\s*IF\s*:\s*([\d.]+)\s*(?:,\s*(Top[^)]*?))?\s*\)", t, re.I)
    if m:
        try:
            info["impact_factor"] = float(m.group(1))
        except ValueError:
            pass
        if m.group(2):
            info["journal_rank"] = m.group(2).strip()
        t = (t[:m.start()] + t[m.end():]).strip()

    # 별도 괄호로 떨어져 있는 순위 표기도 회수
    if info["journal_rank"] is None:
        m = re.search(r"\((Top\s[^)]*?journal[^)]*?)\)", t, re.I)
        if m:
            info["journal_rank"] = m.group(1).strip()
            t = (t[:m.start()] + t[m.end():]).strip()

    # '(*corresponding author)' 같은 주석 제거 (저자 마커에서 이미 반영됨)
    t = re.sub(r"\(\s*\*+\s*corresponding\s+author[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\(\s*\++\s*(co-first|equal)[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip().strip(",").strip()

    # 저널 권(호) (연도) 페이지
    m = re.search(
        r"^(?P<journal>.+?)\s+(?P<vol>\d+)\s*(?:\(\s*(?P<issue>[^)]{1,20}?)\s*\))?"
        r"\s*\(\s*(?P<year>(?:19|20)\d{2})\s*\)\s*(?P<pages>[0-9]+(?:\s*-\s*[0-9]+)?|[A-Za-z0-9.\-]+)?",
        t)
    if m:
        info["journal"] = m.group("journal").strip().strip(",")
        info["volume"] = m.group("vol")
        info["issue"] = m.group("issue")
        info["year"] = int(m.group("year"))
        if m.group("pages"):
            info["pages"] = re.sub(r"\s*-\s*", "-", m.group("pages").strip().strip("."))
        return info, True

    # 권 정보 없이 연도만 있는 경우 (단행본 등)
    m = re.search(r"\(\s*((?:19|20)\d{2})\s*\)", t)
    if m:
        info["year"] = int(m.group(1))
        journal = t[:m.start()].strip().strip(",")
        info["journal"] = journal or None
        rest = t[m.end():].strip()
        if rest:
            info["pages"] = rest.strip(",.").strip() or None
        return info, True

    return info, False


def parse_book_tail(tail):
    """단행본/북챕터용. 저널 논문과 서지 형식이 다르다.

        '. In Osmosis Engineering (pp. 17-52). Elsevier.'  (북챕터)
        ', IWA Publishing'                                 (단행본)
    """
    t = norm(tail)
    t = re.sub(r"^[,.;]\s*", "", t)
    info = {"journal": None, "volume": None, "issue": None, "year": None,
            "pages": None, "impact_factor": None, "journal_rank": None,
            "publisher": None}

    m = re.search(r"\(\s*((?:19|20)\d{2})\s*\)", t)
    if m:
        info["year"] = int(m.group(1))
        t = (t[:m.start()] + t[m.end():]).strip()

    m = re.search(r"\(\s*pp?\.\s*([0-9]+\s*-\s*[0-9]+)\s*\)", t, re.I)
    if m:
        info["pages"] = re.sub(r"\s*-\s*", "-", m.group(1))
        t = (t[:m.start()] + t[m.end():]).strip()

    # 'In <책이름>. <출판사>.' 형태
    m = re.match(r"^In\s+(.+?)\s*\.\s*(.*)$", t, re.I)
    if m:
        info["journal"] = m.group(1).strip().strip(".,")
        info["publisher"] = m.group(2).strip().strip(".,") or None
        return info, True

    m = re.match(r"^In\s+(.+)$", t, re.I)
    if m:
        info["journal"] = m.group(1).strip().strip(".,")
        return info, True

    rest = t.strip().strip(".,").strip()
    if rest:
        info["publisher"] = rest
        return info, True
    return info, False


def split_doi(href):
    """DOI 문자열과 그 외 URL 을 구분한다."""
    if not href:
        return None, None
    href = href.strip()
    m = re.search(r"(?:doi\.org/|dx\.doi\.org/)(10\.\d{4,9}/\S+)", href, re.I)
    if m:
        return m.group(1).rstrip("/"), None
    # pubs.acs.org/doi/10.1021/... 처럼 경로에 DOI 가 들어있는 경우
    m = re.search(r"/doi/(?:abs/|full/)?(10\.\d{4,9}/\S+)", href, re.I)
    if m:
        return m.group(1).rstrip("/"), href
    return None, href


def heading_info(text):
    """헤딩에서 (연도, section) 을 뽑는다.

    '2026'              -> (2026, None)      순수 연도면 section 없음
    '2023 (Before HYU)' -> (2023, 원문)
    'Before CNU (~2021)'-> (None, 원문)
    """
    t = norm(text)
    if re.fullmatch(r"(?:19|20)\d{2}", t):
        return int(t), None
    m = re.match(r"^((?:19|20)\d{2})\b", t)
    if m:
        return int(m.group(1)), t
    if re.search(r"(?:19|20)\d{2}", t):
        return None, t
    return None, None


def parse_page(slug, pub_type):
    path = os.path.join(RAW, slug + ".html")
    if not os.path.exists(path):
        failures.append("%s : raw HTML 없음 (%s)" % (slug, path))
        return []

    soup = BeautifulSoup(io.open(path, encoding="utf-8").read(), "lxml")
    nodes = soup.select("p.zfr3Q, h1, h2, h3, h4")

    items = []
    cur_year, cur_section = None, None
    first_heading_seen = False

    for node in nodes:
        text = norm(node.get_text(""))
        if not text:
            continue

        if node.name != "p":
            if not first_heading_seen:
                first_heading_seen = True          # 페이지 제목은 건너뛴다
                continue
            y, sec = heading_info(text)
            if y is not None or sec is not None:
                cur_year, cur_section = y, sec
            continue

        m = re.match(r"^\((\d+)\)\s*(.*)$", text, re.S)
        if not m:
            continue                                # 번호 없는 문단은 항목이 아니다
        pub_id = int(m.group(1))

        a = node.find("a")
        if a is None:
            failures.append("%s #%d : <a> 없음 -> %s" % (slug, pub_id, text[:120]))
            continue

        title = norm(a.get_text(""))
        full = norm(node.get_text(""))
        anchor = title

        # <a> 앞/뒤 텍스트로 저자와 서지정보를 가른다
        pos = full.find(anchor)
        if pos == -1:
            failures.append("%s #%d : 제목을 본문에서 찾지 못함 -> %s" % (slug, pub_id, title[:100]))
            continue
        before = full[:pos]
        after = full[pos + len(anchor):]

        before = re.sub(r"^\(\d+\)\s*", "", before)
        authors = parse_authors(before)
        if not authors:
            failures.append("%s #%d : 저자 파싱 실패 -> %s" % (slug, pub_id, before[:120]))

        if pub_type in ("book", "book-chapter"):
            info, ok = parse_book_tail(after)
        else:
            info, ok = parse_tail(after)
        if not ok:
            failures.append("%s #%d : 서지정보 파싱 실패 -> %s" % (slug, pub_id, after[:150]))

        doi, url = split_doi(a.get("href"))
        year = info["year"] or cur_year
        if year is None:
            failures.append("%s #%d : 연도 확인 불가" % (slug, pub_id))

        items.append({
            "id": pub_id,
            "type": pub_type,
            "title": title,
            "authors": authors,
            "year": year,
            "journal": info["journal"],
            "volume": info["volume"],
            "issue": info["issue"],
            "pages": info["pages"],
            "doi": doi,
            "url": url,
            "publisher": info.get("publisher"),
            "impact_factor": info["impact_factor"],
            "journal_rank": info["journal_rank"],
            "section": cur_section,
        })

    return items


def dump_yaml(items):
    """읽기 좋은 순서로 직접 직렬화한다 (yaml.dump 는 키 순서와 인용부호가 지저분해진다)."""
    def q(v):
        if v is None:
            return "null"
        s = str(v)
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    out = [
        "# 논문 목록 — scripts/parse_publications.py 가 구 홈페이지에서 생성.",
        "# 직접 고쳐도 되지만, 스크립트를 다시 돌리면 덮어쓰인다.",
        "#",
        "# authors[].corresponding : 원본의 * 표기 (교신저자)",
        "# authors[].co_first      : 원본의 + 또는 dagger 표기 (공동 제1저자)",
        "# doi                     : DOI 문자열만 (URL 아님). 링크는 https://doi.org/{doi}",
        "# url                     : DOI 가 아닌 링크(출판사 페이지 등)",
        "# section                 : '2023 (Before HYU)' 처럼 소속 이력이 표기된 헤딩. 없으면 null",
        "# id                      : 구 홈페이지의 원본 순번 (재정렬해도 보존)",
        "# publisher               : 단행본/북챕터 출판사. 저널 논문은 null",
        "",
    ]
    for it in items:
        out.append("- id: %d" % it["id"])
        out.append("  type: %s" % it["type"])
        out.append("  title: %s" % q(it["title"]))
        out.append("  year: %s" % (it["year"] if it["year"] is not None else "null"))
        out.append("  authors:")
        for a in it["authors"]:
            out.append("    - name: %s" % q(a["name"]))
            out.append("      corresponding: %s" % ("true" if a["corresponding"] else "false"))
            out.append("      co_first: %s" % ("true" if a["co_first"] else "false"))
        for key in ("journal", "volume", "issue", "pages", "publisher", "doi", "url", "journal_rank", "section"):
            out.append("  %s: %s" % (key, q(it[key]) if it[key] is not None else "null"))
        out.append("  impact_factor: %s" % (it["impact_factor"] if it["impact_factor"] is not None else "null"))
        out.append("")
    return "\n".join(out)


def main():
    all_items = []
    per_page = []
    for slug, pub_type in SOURCES:
        before_fail = len(failures)
        items = parse_page(slug, pub_type)
        per_page.append((slug, len(items), len(failures) - before_fail))
        all_items.extend(items)

    # 연도 내림차순, 같은 해 안에서는 원본 순번 내림차순
    all_items.sort(key=lambda x: (-(x["year"] or 0), -x["id"]))

    data_dir = os.path.join(ROOT, "_data")
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
    io.open(os.path.join(data_dir, "publications.yml"), "w",
            encoding="utf-8", newline="\n").write(dump_yaml(all_items))

    with io.open(FAILED, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n=== parse_publications.py @ %s ===\n"
                % datetime.datetime.now().isoformat(timespec="seconds"))
        if failures:
            for line in failures:
                f.write("  " + line + "\n")
        else:
            f.write("  (실패 항목 없음)\n")

    print("페이지별 결과")
    for slug, n, nf in per_page:
        print("  %-30s 성공 %3d  실패 %d" % (slug, n, nf))
    print("\n  총 %d건 -> _data/publications.yml" % len(all_items))
    print("  실패 %d건 -> scripts/failed.log" % len(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
