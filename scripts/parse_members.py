# -*- coding: utf-8 -*-
"""scripts/raw/people-*.html -> _data/members.yml + scripts/raw/photo_manifest.json

이메일은 평문으로 넣지 않는다. user 와 domain 을 분리해 저장하고,
템플릿에서 JavaScript 로 합쳐 렌더링한다 (스팸 봇 수집 방지).

졸업생(alumni)은 사진과 이름 자체가 개인정보이므로 needs_consent: true 를 달고
scripts/consent-check.md 에 목록을 남긴다. 동의 전에는 템플릿에서 렌더링하지 않는다.

사진 URL 은 photo_manifest.json 에만 남기고 YAML 에는 로컬 경로만 넣는다.
구 사이트가 사라져도 새 사이트가 깨지지 않도록 하기 위해서다.
"""
import io
import os
import re
import sys
import json
import datetime
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")
FAILED = os.path.join(HERE, "failed.log")

PAGES = [
    ("people-principle-investigator", "pi"),
    ("people-graduates",              None),          # Degree 문자열로 판정
    ("people-undergraduates",         "undergraduate"),
    ("people-alumni",                 "alumni"),
]

failures = []
photo_manifest = {}

# 본인 동의를 확인한 졸업생. 여기 있으면 needs_consent 를 붙이지 않는다.
# (파서를 --force 로 다시 돌려도 동의 확인 결과가 유지되도록 여기에 둔다)
# 확인일: 2026-08-07
CONSENT_GRANTED = {
    "Suji Son",
    "Gyu Sang Cho",
}


def norm(s):
    return re.sub(r"[ \t]+", " ", (s or "").replace("\xa0", " ")).strip()


def slugify(name_en):
    s = (name_en or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "unknown"


def banner_urls():
    """모든 페이지에 공통으로 등장하는 이미지는 사이트 배너/로고다. 인물 사진이 아니다."""
    sets = []
    for slug, _ in PAGES:
        p = os.path.join(RAW, slug + ".html")
        if not os.path.exists(p):
            continue
        soup = BeautifulSoup(io.open(p, encoding="utf-8").read(), "lxml")
        sets.append({i.get("src") for i in soup.select("img")
                     if i.get("src") and "googleusercontent" in i.get("src")})
    if not sets:
        return set()
    common = set.intersection(*sets) if len(sets) > 1 else set()
    return common


def group_from_degree(degree, page_default):
    if page_default:
        return page_default
    d = (degree or "").lower()
    if "integrated" in d:
        return "integrated"
    if "ph.d" in d or "phd" in d:
        return "phd"
    if "master" in d or "m.s" in d:
        return "master"
    if "b.s" in d or "undergrad" in d:
        return "undergraduate"
    return None


def split_email(text):
    m = re.search(r"([A-Za-z0-9._%+\-]+)@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})", text or "")
    if not m:
        return None, None
    return m.group(1), m.group(2)


def parse_people_page(slug, page_default, banners):
    """h2 = 사람, 그 다음 p 들이 속성. 사진은 각 h2 바로 앞의 이미지."""
    path = os.path.join(RAW, slug + ".html")
    if not os.path.exists(path):
        failures.append("%s : raw HTML 없음" % slug)
        return []
    soup = BeautifulSoup(io.open(path, encoding="utf-8").read(), "lxml")

    # 문서 순서대로 훑으며 h2 직전의 이미지를 그 사람의 사진으로 본다
    flow = soup.find_all(["h1", "h2", "p", "img"])
    members = []
    pending_photo = None
    cur = None
    sub_group = None

    for el in flow:
        if el.name == "img":
            src = el.get("src") or ""
            if "googleusercontent" in src and src not in banners:
                pending_photo = src
            continue

        text = norm(el.get_text(""))
        if not text:
            continue

        if el.name == "h2":
            m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", text)
            if m:
                name_ko, name_en = m.group(1).strip(), m.group(2).strip()
            else:
                name_ko, name_en = None, text
                failures.append("%s : 이름에서 한글/영문 분리 실패 -> %s" % (slug, text))
            cur = {
                "name_ko": name_ko, "name_en": name_en,
                "group": page_default or sub_group, "degree": None, "started": None,
                "email_user": None, "email_domain": None,
                "research_areas": [], "former_status": None,
                "photo": None, "_photo_src": pending_photo,
            }
            pending_photo = None
            members.append(cur)
            continue

        if el.name != "p":
            continue

        # 그룹 소제목("Ph.D course", "Master course")은 사람 블록 사이에 끼어 나온다.
        # 만나면 현재 사람을 닫아야 앞사람의 research area 로 흡수되지 않는다.
        if re.match(r"^(?:Ph\.?D|Master|M\.?S|B\.?S|Integrated)[\w\s./]*course$", text, re.I):
            sub_group = group_from_degree(text, None)
            cur = None
            continue
        if cur is None:
            continue

        m = re.match(r"^Degree\s*(.*)$", text, re.I)
        if m:
            deg = m.group(1).strip()
            cur["degree"] = deg
            ms = re.search(r"\(\s*((?:19|20)\d{2}\.\d{1,2})\s*~", deg)
            if ms:
                y, mo = ms.group(1).split(".")
                cur["started"] = "%s.%02d" % (y, int(mo))
            g = group_from_degree(deg, page_default)
            if g:
                cur["group"] = g
            continue

        m = re.match(r"^Contact\s*(.*)$", text, re.I)
        if m:
            u, d = split_email(m.group(1))
            if u:
                cur["email_user"], cur["email_domain"] = u, d
            else:
                failures.append("%s / %s : Contact 파싱 실패 -> %s"
                                % (slug, cur["name_en"], text[:80]))
            continue

        # 'Research area' 라벨은 값과 붙어서 나온다 (span 병합 부작용)
        m = re.match(r"^Research\s*area(?:s(?=[\s:\-]))?\s*[:\-]?\s*(.*)$", text, re.I)
        if m:
            v = m.group(1).strip()
            if v:
                cur["research_areas"].append(v)
            cur["_in_research"] = True
            continue

        if page_default == "alumni":
            cur["former_status"] = text
            continue

        if cur.get("_in_research"):
            cur["research_areas"].append(text)

    for m in members:
        m.pop("_in_research", None)
        if not m["group"]:
            failures.append("%s / %s : group 판정 실패 (degree=%s)"
                            % (slug, m["name_en"], m["degree"]))
    return members


def parse_pi_page(banners):
    """PI 페이지는 형식이 다르다. h1 이 이름이고, 이력이 문단으로 나열된다."""
    path = os.path.join(RAW, "people-principle-investigator.html")
    soup = BeautifulSoup(io.open(path, encoding="utf-8").read(), "lxml")

    flow = soup.find_all(["h1", "h2", "p", "img"])
    photo = None
    name_en = None
    lines = []
    seen_title = False
    for el in flow:
        if el.name == "img":
            src = el.get("src") or ""
            if "googleusercontent" in src and src not in banners:
                photo = photo or src
            continue
        text = norm(el.get_text(""))
        if not text:
            continue
        if el.name in ("h1", "h2"):
            if not seen_title:
                seen_title = True            # 페이지 제목 'Principle Investigator'
                continue
            if name_en is None:
                name_en = re.sub(r",\s*Ph\.?D\.?\s*$", "", text, flags=re.I).strip()
            continue
        if name_en:
            lines.append(text)

    if not name_en:
        failures.append("PI : 이름을 찾지 못함")
        return []

    rec = {
        "name_ko": None, "name_en": name_en, "group": "pi",
        "degree": None, "started": None,
        "email_user": None, "email_domain": None,
        "research_areas": [], "former_status": None,
        "title": None, "department": None, "university": None, "tel": None,
        "education": [], "experience": [], "activities": [],
        "photo": None, "_photo_src": photo,
    }

    section = None
    for t in lines:
        if re.match(r"^Education\b", t, re.I):
            section = "education"; continue
        if re.match(r"^Professional\s+Experience\b", t, re.I):
            section = "experience"; continue
        if re.match(r"^Professional\s+Activities", t, re.I):
            section = "activities"; continue
        if re.match(r"^Research\s*(area|interest)", t, re.I):
            section = "research"; continue

        m = re.match(r"^Tel\s*[:：]\s*(.+)$", t, re.I)
        if m:
            rec["tel"] = m.group(1).strip(); continue
        m = re.match(r"^E-?mail\s*[:：]\s*(.+)$", t, re.I)
        if m:
            u, d = split_email(m.group(1))
            rec["email_user"], rec["email_domain"] = u, d
            continue

        if section is None:
            if rec["title"] is None and re.search(r"professor", t, re.I):
                rec["title"] = t
            elif rec["department"] is None and re.search(r"department|school", t, re.I):
                rec["department"] = t
            elif rec["university"] is None and re.search(r"universit", t, re.I):
                rec["university"] = t
        elif section == "research":
            rec["research_areas"].append(t)
        else:
            rec[section].append(t)

    return [rec]


def q(v):
    if v is None:
        return "null"
    s = str(v)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump_yaml(members):
    out = [
        "# 연구실 구성원 — scripts/parse_members.py 가 구 홈페이지에서 생성.",
        "#",
        "# email_user / email_domain",
        "#   이메일을 평문으로 두지 않기 위해 분리 저장한다.",
        "#   템플릿에서 JavaScript 로 합쳐 렌더링하므로 HTML 소스에는 주소가 남지 않는다.",
        "#   YAML 을 직접 고칠 때도 절대 한 줄로 합치지 말 것.",
        "#",
        "# ⚠ 이 파일은 손으로 고쳐도 된다. 다만 scripts/parse_members.py 를 다시 돌리면",
        "#   덮어써진다. 그래서 그 스크립트는 --force 없이는 실행되지 않게 해 두었다.",
        "#   취미(hobby)와 사진(photo)은 여기서 직접 채우는 항목이다.",
        "#",
        "# group : pi | phd | integrated | master | undergraduate | alumni",
        "# hobby : 본인이 직접 적는 칸. 비워 두면 화면에 나오지 않는다.",
        "# photo : 사진을 넣는 방법",
        "#   1) 이미지를 assets/img/members/<photo_slug>.webp 로 올린다",
        "#      (정사각형 권장. scripts/optimize_news_images.py 로 변환 가능)",
        "#   2) 아래 photo 를 그 경로로 바꾼다. 예: /assets/img/members/kiho-park.webp",
        "#   null 인 동안에는 이름 이니셜 자리표시자가 대신 나온다.",
        "#   실제 파일이 없는 경로를 적으면 사이트에 깨진 이미지가 뜨니 주의.",
        "# needs_consent : 본인 동의 확인 전까지 템플릿에서 렌더링하지 않는다.",
        "#                 scripts/consent-check.md 참조.",
        "",
    ]
    for m in members:
        out.append("- name_en: %s" % q(m["name_en"]))
        out.append("  name_ko: %s" % q(m["name_ko"]))
        out.append("  group: %s" % q(m["group"]))
        out.append("  degree: %s" % q(m["degree"]))
        out.append("  started: %s" % q(m["started"]))
        out.append("  email_user: %s" % q(m["email_user"]))
        out.append("  email_domain: %s" % q(m["email_domain"]))
        out.append("  photo: %s" % (q(m["photo"]) if m["photo"] else "null"))
        out.append("  photo_slug: %s" % q(m.get("photo_slug")))
        if m["group"] != "pi":
            out.append("  hobby: %s" % q(m.get("hobby") or ""))
        if m.get("needs_consent"):
            out.append("  needs_consent: true")
        if m.get("former_status"):
            out.append("  former_status: %s" % q(m["former_status"]))
        for key in ("title", "department", "university", "tel"):
            if m.get(key):
                out.append("  %s: %s" % (key, q(m[key])))
        if m["research_areas"]:
            out.append("  research_areas:")
            for r in m["research_areas"]:
                out.append("    - %s" % q(r))
        else:
            out.append("  research_areas: []")
        for key in ("education", "experience", "activities"):
            if m.get(key):
                out.append("  %s:" % key)
                for r in m[key]:
                    out.append("    - %s" % q(r))
        out.append("")
    return "\n".join(out)


def main():
    # _data/members.yml 은 사람이 직접 고치는 파일이다 (취미, 사진 경로).
    # 이 스크립트는 구 홈페이지에서 새로 생성하므로 그 편집분을 지운다.
    # 실수로 날리지 않도록 --force 를 요구한다.
    target = os.path.join(ROOT, "_data", "members.yml")
    if os.path.exists(target) and "--force" not in sys.argv:
        print("_data/members.yml 이 이미 있다. 다시 생성하면 손으로 적은")
        print("취미와 사진 경로가 사라진다.")
        print("정말 다시 만들려면:  python scripts/parse_members.py --force")
        return 1

    banners = banner_urls()
    members = []
    per_page = []

    for slug, default in PAGES:
        before = len(failures)
        if slug == "people-principle-investigator":
            got = parse_pi_page(banners)
        else:
            got = parse_people_page(slug, default, banners)
        per_page.append((slug, len(got), len(failures) - before))
        members.extend(got)

    # 사진 경로 확정 + 매니페스트
    #
    # 중요: 실제 파일이 저장소에 있을 때만 photo 에 경로를 넣는다.
    # 없는 경로를 넣으면 사이트에 깨진 이미지가 뜬다.
    # 파일이 없으면 null 로 두고, 템플릿이 이니셜 자리표시자를 그린다.
    for m in members:
        slug = slugify(m["name_en"])
        src = m.pop("_photo_src", None)
        rel = "assets/img/members/%s.webp" % slug
        if src:
            photo_manifest[slug] = {"name_en": m["name_en"], "source": src, "local": rel}
        m["photo"] = ("/" + rel) if os.path.exists(os.path.join(ROOT, rel)) else None
        m["photo_slug"] = slug           # 사진을 올릴 때 쓸 파일명
        if m["group"] != "pi":
            m.setdefault("hobby", "")    # 본인이 직접 채우는 항목
        if m["group"] == "alumni" and m["name_en"] not in CONSENT_GRANTED:
            m["needs_consent"] = True

    order = {"pi": 0, "phd": 1, "integrated": 2, "master": 3, "undergraduate": 4, "alumni": 5}
    members.sort(key=lambda x: (order.get(x["group"], 9), x["started"] or "", x["name_en"]))

    data_dir = os.path.join(ROOT, "_data")
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
    io.open(os.path.join(data_dir, "members.yml"), "w",
            encoding="utf-8", newline="\n").write(dump_yaml(members))
    json.dump(photo_manifest, io.open(os.path.join(RAW, "photo_manifest.json"), "w",
                                      encoding="utf-8"), ensure_ascii=False, indent=2)

    # 동의 확인 목록
    need = [m for m in members if m.get("needs_consent")]
    doc = ["# 동의 확인 필요 목록", "",
           "생성: %s" % datetime.datetime.now().isoformat(timespec="seconds"), "",
           "아래 항목은 **본인 동의를 확인하기 전까지 웹사이트에 렌더링하지 않는다.**",
           "`_data/members.yml` 에 `needs_consent: true` 로 표시되어 있고,",
           "템플릿이 이 플래그가 붙은 항목을 건너뛴다.", "",
           "동의를 받은 뒤에는 해당 항목의 `needs_consent` 줄을 지우면 노출된다.", ""]
    if need:
        doc += ["| 이름 | 그룹 | 사진 | 이메일 | 비고 |", "|---|---|---|---|---|"]
        for m in need:
            doc.append("| %s (%s) | %s | %s | %s | %s |" % (
                m["name_ko"] or "-", m["name_en"], m["group"],
                "있음" if m["photo"] else "없음",
                "있음" if m["email_user"] else "없음",
                m.get("former_status") or ""))
        doc += ["", "확인할 것", "",
                "- 사진을 새 사이트에 계속 게시해도 되는지",
                "- 이름(한글/영문) 공개 여부",
                "- 현재 소속을 표기할지, 표기한다면 최신 정보가 맞는지"]
    else:
        doc.append("(현재 동의 확인이 필요한 항목 없음)")
    io.open(os.path.join(HERE, "consent-check.md"), "w",
            encoding="utf-8", newline="\n").write("\n".join(doc) + "\n")

    with io.open(FAILED, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n=== parse_members.py @ %s ===\n"
                % datetime.datetime.now().isoformat(timespec="seconds"))
        f.write("".join("  %s\n" % x for x in failures) if failures else "  (실패 항목 없음)\n")

    print("페이지별 결과")
    for slug, n, nf in per_page:
        print("  %-32s 성공 %2d  실패 %d" % (slug, n, nf))
    print("\n  총 %d명 -> _data/members.yml" % len(members))
    print("  사진 URL %d건 -> scripts/raw/photo_manifest.json" % len(photo_manifest))
    print("  동의 확인 %d명 -> scripts/consent-check.md" % len(need))
    from collections import Counter
    print("  그룹 분포: %s" % dict(Counter(m["group"] for m in members)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
