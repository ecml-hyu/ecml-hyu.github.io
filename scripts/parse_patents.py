# -*- coding: utf-8 -*-
"""scripts/raw/patents.html -> _data/patents.yml

한 항목의 형태:
    (9) 제목 (Patent #번호, 관할, 상태)

제목 자체에 괄호와 쉼표가 들어있는 경우가 있어(예: "(AF4)", "1,1,2,2,...")
맨 뒤 괄호 묶음을 먼저 떼어낸 뒤 제목을 자른다.

순번은 'Submitted patents' / 'Registered patents' 섹션별로 따로 매겨진다.
(양쪽에 (9) 가 하나씩 있다) 그래서 status 와 함께 봐야 구분된다.
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


def norm(s):
    s = (s or "").replace("\xa0", " ")
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[ \t]+", " ", s).strip()


def parse():
    path = os.path.join(RAW, "patents.html")
    if not os.path.exists(path):
        failures.append("patents : raw HTML 없음")
        return []

    soup = BeautifulSoup(io.open(path, encoding="utf-8").read(), "lxml")
    items = []
    section = None
    first_heading = False

    for node in soup.select("p.zfr3Q, h1, h2, h3, h4"):
        text = norm(node.get_text(""))
        if not text:
            continue

        if node.name != "p":
            if not first_heading:
                first_heading = True          # 페이지 제목 'Patents'
                continue
            section = text                     # 'Submitted patents' / 'Registered patents'
            continue

        m = re.match(r"^\((\d+)\)\s*(.+)$", text, re.S)
        if not m:
            continue
        pid, rest = int(m.group(1)), m.group(2).strip()

        # 맨 뒤 괄호 묶음이 서지정보다. 제목 안의 괄호와 헷갈리지 않게 뒤에서 자른다.
        tail = re.search(r"\(([^()]*)\)\s*$", rest)
        if not tail:
            failures.append("patents #%d : 괄호 정보 없음 -> %s" % (pid, rest[:100]))
            continue
        title = rest[:tail.start()].strip()
        parts = [x.strip() for x in tail.group(1).split(",")]
        if len(parts) < 3:
            failures.append("patents #%d : 괄호 안 항목이 3개 미만 -> %s" % (pid, tail.group(1)))
            continue

        number = re.sub(r"^Patent\s*#\s*", "", parts[0], flags=re.I).strip()
        jurisdiction = parts[1]
        status = parts[-1].lower()

        a = node.find("a")
        url = a.get("href").strip() if a and a.get("href") else None

        # 한국 특허 링크는 doi.org 형태지만 실제 DOI 가 아니라 KIPRIS 출원번호다.
        items.append({
            "id": pid,
            "title": title,
            "number": number,
            "jurisdiction": jurisdiction,
            "status": status,
            "section": section,
            "url": url,
        })

    return items


def q(v):
    if v is None:
        return "null"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(items):
    out = [
        "# 특허 목록 — scripts/parse_patents.py 가 구 홈페이지에서 생성.",
        "#",
        "# status       : registered(등록) / submitted(출원)",
        "# number       : 특허번호. 한국은 10-XXXXXXX, 미국은 USXXXXXXX 형태",
        "# jurisdiction : Korea / US Patent / China / PCT",
        "# id           : 구 홈페이지의 원본 순번.",
        "#                주의 — 출원/등록 섹션별로 따로 매겨져 (9)번이 둘 있다.",
        "#                고유 식별은 number 로 할 것.",
        "# url          : 특허 원문 링크. 한국 건은 doi.org 형태지만 실제 DOI 가 아니라",
        "#                KIPRIS 출원번호 리다이렉트다.",
        "",
    ]
    for it in items:
        out.append("- id: %d" % it["id"])
        for k in ("title", "number", "jurisdiction", "status", "section", "url"):
            out.append("  %s: %s" % (k, q(it[k])))
        out.append("")
    return "\n".join(out)


def main():
    items = parse()
    # 등록건 먼저, 각 그룹 안에서는 순번 내림차순
    order = {"registered": 0, "submitted": 1}
    items.sort(key=lambda x: (order.get(x["status"], 9), -x["id"]))

    data_dir = os.path.join(ROOT, "_data")
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
    io.open(os.path.join(data_dir, "patents.yml"), "w",
            encoding="utf-8", newline="\n").write(dump(items))

    with io.open(FAILED, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n=== parse_patents.py @ %s ===\n"
                % datetime.datetime.now().isoformat(timespec="seconds"))
        f.write("".join("  %s\n" % x for x in failures) if failures else "  (실패 항목 없음)\n")

    from collections import Counter
    print("특허 %d건 -> _data/patents.yml" % len(items))
    print("  상태별: %s" % dict(Counter(x["status"] for x in items)))
    print("  관할별: %s" % dict(Counter(x["jurisdiction"] for x in items)))
    print("  실패 %d건" % len(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
