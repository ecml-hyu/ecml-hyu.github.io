# -*- coding: utf-8 -*-
"""scripts/raw/projects.html -> _data/projects.yml

한 과제의 형태:
    <h1>한글 과제명</h1>
    <p>(English title)</p>
    <p>공동7: ...</p>          <- 세부과제/역할. 없는 경우가 많다
    <p>지원기관: 기관명 (부처)</p>
    <p>연구기간: 2024.04.01. ~ 2029.03.28.</p>

'Ongoing projects' / 'Terminated projects' 헤딩으로 진행 여부를 나눈다.
사진은 옮기지 않는다 (담당자가 직접 넣기로 함).
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

failures = []

SECTIONS = {"ongoing projects": "ongoing", "terminated projects": "terminated"}


def norm(s):
    s = (s or "").replace("\xa0", " ")
    s = s.replace("−", "-").replace("–", "-").replace("—", "-").replace("~", "~")
    return re.sub(r"[ \t]+", " ", s).strip()


def parse_period(text):
    """'연구기간: 2024.04.01. ~ 2029.03.28.' -> ('2024.04.01', '2029.03.28')"""
    dates = re.findall(r"((?:19|20)\d{2})\.\s*(\d{1,2})\.\s*(\d{1,2})", text)
    out = ["%s.%02d.%02d" % (y, int(m), int(d)) for y, m, d in dates]
    if len(out) >= 2:
        return out[0], out[1]
    if len(out) == 1:
        return out[0], None
    return None, None


def parse():
    path = os.path.join(RAW, "projects.html")
    if not os.path.exists(path):
        failures.append("projects : raw HTML 없음")
        return []

    soup = BeautifulSoup(io.open(path, encoding="utf-8").read(), "lxml")
    nodes = soup.select("p.zfr3Q, h1, h2, h3, h4")

    items = []
    status = None
    cur = None
    page_title_seen = False

    for node in nodes:
        text = norm(node.get_text(""))
        if not text:
            continue

        if node.name != "p":
            key = text.lower()
            if not page_title_seen and key == "projects":
                page_title_seen = True          # 페이지 제목
                continue
            if key in SECTIONS:
                status = SECTIONS[key]
                cur = None
                continue
            # 그 밖의 헤딩은 과제명
            cur = {
                "title_ko": text, "title_en": None, "role": None,
                "funder": None, "ministry": None,
                "start": None, "end": None, "status": status,
            }
            if status is None:
                failures.append("projects : '%s' 가 진행/종료 구분 앞에 나왔다" % text[:60])
            items.append(cur)
            continue

        if cur is None:
            continue

        m = re.match(r"^지원기관\s*[:：]\s*(.+)$", text)
        if m:
            v = m.group(1).strip()
            # '한국연구재단 (과학기술정보통신부)' 처럼 괄호 안에 부처가 온다
            mm = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", v)
            if mm:
                cur["funder"], cur["ministry"] = mm.group(1).strip(), mm.group(2).strip()
            else:
                cur["funder"] = v
            continue

        m = re.match(r"^연구기간\s*[:：]\s*(.+)$", text)
        if m:
            cur["start"], cur["end"] = parse_period(m.group(1))
            if not cur["start"]:
                failures.append("projects / %s : 연구기간 파싱 실패 -> %s"
                                % (cur["title_ko"][:40], m.group(1)[:60]))
            continue

        # 괄호로 감싸인 줄이 영문 과제명
        m = re.match(r"^\((.+)\)\s*$", text, re.S)
        if m and cur["title_en"] is None:
            cur["title_en"] = norm(m.group(1))
            continue

        # 그 밖의 줄은 세부과제/역할 설명 (예: '공동7: ...')
        if cur["role"] is None:
            cur["role"] = text
        else:
            cur["role"] += " " + text

    for it in items:
        if not it["title_en"]:
            failures.append("projects / %s : 영문 과제명 없음" % it["title_ko"][:40])
        if not it["funder"]:
            failures.append("projects / %s : 지원기관 없음" % it["title_ko"][:40])
    return items


def q(v):
    if v is None:
        return "null"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(items):
    out = [
        "# 연구 과제 — scripts/parse_projects.py 가 구 홈페이지에서 생성.",
        "#",
        "# status    : ongoing(진행중) / terminated(종료)",
        "# title_ko  : 국문 과제명",
        "# title_en  : 영문 과제명",
        "# role      : 세부과제나 담당 역할. 없으면 null",
        "# funder    : 지원기관 (예: 한국연구재단)",
        "# ministry  : 소관 부처. 지원기관 뒤 괄호 안 값. 없으면 null",
        "# start/end : 연구기간. YYYY.MM.DD 형식",
        "#",
        "# 사진은 옮기지 않았다. 필요하면 담당자가 직접 추가한다.",
        "",
    ]
    for it in items:
        out.append("- title_ko: %s" % q(it["title_ko"]))
        for k in ("title_en", "role", "funder", "ministry", "start", "end", "status"):
            out.append("  %s: %s" % (k, q(it[k])))
        out.append("")
    return "\n".join(out)


def main():
    items = parse()
    # 진행중 먼저, 각 그룹 안에서는 시작일 최신순
    order = {"ongoing": 0, "terminated": 1}
    items.sort(key=lambda x: (order.get(x["status"], 9),
                              "" if not x["start"] else x["start"]), reverse=False)
    items.sort(key=lambda x: (order.get(x["status"], 9),
                              "0000" if not x["start"] else x["start"]))
    grouped = []
    for st in ("ongoing", "terminated"):
        grp = [x for x in items if x["status"] == st]
        grp.sort(key=lambda x: x["start"] or "", reverse=True)
        grouped.extend(grp)

    data_dir = os.path.join(ROOT, "_data")
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
    io.open(os.path.join(data_dir, "projects.yml"), "w",
            encoding="utf-8", newline="\n").write(dump(grouped))

    with io.open(FAILED, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n=== parse_projects.py @ %s ===\n"
                % datetime.datetime.now().isoformat(timespec="seconds"))
        f.write("".join("  %s\n" % x for x in failures) if failures else "  (실패 항목 없음)\n")

    from collections import Counter
    print("과제 %d건 -> _data/projects.yml" % len(grouped))
    print("  상태별  : %s" % dict(Counter(x["status"] for x in grouped)))
    print("  지원기관: %s" % dict(Counter(x["funder"] for x in grouped)))
    print("  실패 %d건" % len(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
