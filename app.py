# app_bright.py — AI Sourcing Assistant (Bright, Accessible UI)
# Copy this entire file into `app.py` (or set Streamlit main file path to `app_bright.py`).
# Requires: streamlit==1.33.0

import re
from typing import List, Tuple
import streamlit as st

st.set_page_config(page_title="AI Sourcing Assistant", layout="wide")


# ============================ Role Library (extensible) ============================
ROLE_LIB = {
    "swe": {
        "titles": [
            "Software Engineer", "Software Developer", "SDE", "SDE I", "SDE II",
            "Senior Software Engineer", "Full Stack Engineer", "Backend Engineer",
            "Frontend Engineer", "Platform Engineer"
        ],
        "must": ["python", "java", "go", "microservices", "distributed systems"],
        "nice": ["kubernetes", "docker", "graphql", "gRPC", "aws"],
    },
    "ml": {
        "titles": [
            "Machine Learning Engineer", "ML Engineer", "ML Scientist",
            "Applied Scientist", "Data Scientist", "AI Engineer"
        ],
        "must": ["python", "pytorch", "tensorflow", "mlops", "model deployment"],
        "nice": ["sklearn", "xgboost", "feature store", "mlflow", "sagemaker"],
    },
    "sre": {
        "titles": [
            "Site Reliability Engineer", "SRE", "Reliability Engineer",
            "DevOps Engineer", "Platform Reliability Engineer"
        ],
        "must": ["kubernetes", "terraform", "prometheus", "grafana", "incident response"],
        "nice": ["golang", "python", "aws", "gcp", "oncall"],
    },
}

SMART_NOT = [
    "intern", "internship", "fellow", "bootcamp", "student", "professor",
    "sales", "marketing", "hr", "talent acquisition", "recruiter",
    "customer support", "help desk", "desktop support", "qa tester"
]


# ============================ Helpers ============================
def unique_preserve(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        x2 = (x or "").strip()
        if not x2:
            continue
        key = x2.lower()
        if key not in seen:
            seen.add(key)
            out.append(x2)
    return out


def or_group(items: List[str]) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return ""
    quoted = []
    for i in items:
        if " " in i and not i.startswith('"'):
            quoted.append('"' + i + '"')
        else:
            quoted.append(i)
    return "(" + " OR ".join(quoted) + ")"


def map_title_to_category(title: str) -> str:
    s = (title or "").lower()
    # SRE first
    sre_terms = ["sre", "site reliability", "reliab", "devops", "platform reliability"]
    if any(t in s for t in sre_terms):
        return "sre"
    # ML next
    ml_terms = [
        "machine learning", "ml engineer", "applied scientist",
        "data scientist", "ai engineer", " ml ", "ml-", "ml/"
    ]
    if any(t in s for t in ml_terms):
        return "ml"
    return "swe"


def expand_titles(base_titles: List[str], cat: str) -> List[str]:
    extra: List[str] = []
    if cat == "swe":
        extra = ["Software Eng", "Software Dev", "Full-Stack Engineer",
                 "Backend Developer", "Frontend Developer"]
    elif cat == "ml":
        extra = ["ML Eng", "Machine Learning Specialist",
                 "Applied ML Engineer", "ML Research Engineer"]
    elif cat == "sre":
        extra = ["Reliability Eng", "DevOps SRE", "Platform SRE", "Production Engineer"]
    return unique_preserve(base_titles + extra)


def build_keywords(must: List[str], nice: List[str], nots: List[str], qualifiers: List[str] = None) -> str:
    base = unique_preserve(must + nice)
    if qualifiers:
        base = base + [q for q in qualifiers if q]
    core = or_group(base)
    if not core:
        return ""
    nots2 = unique_preserve(nots)
    if nots2:
        return core + " NOT (" + " OR ".join(nots2) + ")"
    return core


def jd_extract(jd_text: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Minimal extractor: count occurrences of known skills from ROLE_LIB across all roles.
    Returns (must_ex, nice_ex, auto_not).
    """
    jd = (jd_text or "").lower()
    pool = set()
    for role in ROLE_LIB.values():
        for s in role["must"] + role["nice"]:
            pool.add(s.lower())
    counts = {s: jd.count(s) for s in pool}
    ranked = [s for s, c in sorted(counts.items(), key=lambda x: x[1], reverse=True) if c > 0]
    must_ex = ranked[:8]
    nice_ex = ranked[8:16]
    auto_not = []
    for kw in ["intern", "contract", "temporary", "help desk", "desktop support", "qa tester", "graphic designer"]:
        if kw in jd:
            auto_not.append(kw)
    return must_ex, nice_ex, auto_not


def string_health_report(s: str) -> List[str]:
    issues: List[str] = []
    if not s:
        return ["Keywords are empty — add must/nice skills."]
    if len(s) > 900:
        issues.append("Keywords look long (>900 chars); consider trimming.")
    if s.count(" OR ") > 80:
        issues.append("High OR count; remove niche/redundant terms.")
    # Parentheses balance
    depth = 0
    ok = True
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                ok = False
                break
    if depth != 0 or not ok:
        issues.append("Unbalanced parentheses; copy fresh strings or simplify.")
    return issues


def apply_seniority(titles: List[str], level: str) -> List[str]:
    base = []
    for t in titles:
        b = t
        for tok in ["Senior ", "Staff ", "Principal ", "Lead ", "Sr "]:
            b = b.replace(tok, "")
        base.append(b.strip())
    out: List[str] = []
    if level == "All":
        out = titles + base
    elif level == "Associate":
        out = ["Junior " + b for b in base] + base
    elif level == "Mid":
        out = base
    elif level == "Senior+":
        out = ["Senior " + b for b in base] + base
    else:  # Staff/Principal
        out = ["Staff " + b for b in base] + ["Principal " + b for b in base] + ["Lead " + b for b in base] + base
    # dedupe preserve order
    seen, res = set(), []
    for x in out:
        xl = x.lower()
        if xl not in seen:
            seen.add(xl); res.append(x)
    return res[:24]


# ============================ Bright Themes (no dark background) ============================
THEMES = {
    "Sky":    {"grad": "linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)", "bg": "#F8FAFC", "card": "#FFFFFF", "text": "#0F172A", "muted": "#475569", "ring": "#3B82F6", "button": "#2563EB"},
    "Coral":  {"grad": "linear-gradient(135deg, #FB7185 0%, #F59E0B 100%)", "bg": "#FFF7ED", "card": "#FFFFFF", "text": "#111827", "muted": "#6B7280", "ring": "#F97316", "button": "#F97316"},
    "Mint":   {"grad": "linear-gradient(135deg, #34D399 0%, #22D3EE 100%)", "bg": "#ECFEFF", "card": "#FFFFFF", "text": "#0F172A", "muted": "#334155", "ring": "#10B981", "button": "#10B981"},
}


def inject_css(theme_name: str) -> None:
    t = THEMES.get(theme_name, THEMES["Sky"])
    parts = [
        "<style>",
        ":root {",
        "--grad: " + t["grad"] + ";",
        "--bg: " + t["bg"] + ";",
        "--card: " + t["card"] + ";",
        "--text: " + t["text"] + ";",
        "--muted: " + t["muted"] + ";",
        "--ring: " + t["ring"] + ";",
        "--btn: " + t["button"] + ";",
        "--gap: 16px;",
        "--pad: 14px;",
        "--radius: 16px;",
        "--codefs: 12.5px;",
        "--btnpad: 9px 14px;",
        "}",
        ".stApp, [data-testid='stAppViewContainer'] {background: var(--bg); color: var(--text);}",
        "[data-testid='stHeader'] {background: transparent;}",
        ".hero {padding: var(--pad); border-radius: var(--radius); background: var(--card); ",
        "border: 1px solid rgba(0,0,0,.06); box-shadow: 0 6px 24px rgba(2,6,23,.06); margin-bottom: var(--gap);}",
        ".hero h1 {margin: 0; font-size: 28px; font-weight: 800; background: var(--grad); ",
        "-webkit-background-clip: text; background-clip: text; color: transparent;}",
        ".chips {display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px;}",
        ".chip {padding: 6px 10px; border-radius: 999px; font-size: 12px; color: var(--text); ",
        "background: rgba(2,6,23,.04); border: 1px solid rgba(2,6,23,.06);}",
        "input[type='text'], textarea {background: var(--card) !important; color: var(--text) !important; ",
        "border: 1px solid rgba(2,6,23,.08) !important; border-radius: var(--radius) !important;}",
        "input[type='text']:focus, textarea:focus {outline: none !important; border-color: var(--ring) !important; ",
        "box-shadow: 0 0 0 3px rgba(37,99,235,.18) !important;}",
        ".stButton>button, .stDownloadButton>button {background: var(--btn); color: #FFFFFF; font-weight: 700; border: none; ",
        "padding: var(--btnpad); border-radius: 999px; box-shadow: 0 10px 24px rgba(2,6,23,.12);}",
        ".stButton>button:hover, .stDownloadButton>button:hover {filter: brightness(1.05);}",
        ".stButton>button:focus {outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.25);}",
        "pre, code {font-size: var(--codefs) !important;}",
        ".grid {display: grid; gap: var(--gap); grid-template-columns: repeat(12, 1fr);}",
        ".card {grid-column: span 6; background: var(--card); border: 1px solid rgba(2,6,23,.06); ",
        "border-radius: var(--radius); padding: var(--pad); box-shadow: 0 6px 24px rgba(2,6,23,.06);}",
        ".hint {font-size: 12px; color: var(--muted); margin-top: 4px;}",
        ".divider {height: 1px; background: linear-gradient(90deg, transparent, rgba(2,6,23,.15), transparent); margin: 8px 0;}",
        ".tagrow {display:flex; gap:8px; flex-wrap:wrap;}",
        ".tagbtn {background: rgba(2,6,23,.06); border: 1px solid rgba(2,6,23,.1); border-radius: 999px; padding: 6px 10px; font-size: 12px;}",
        "</style>",
    ]
    st.markdown("".join(parts), unsafe_allow_html=True)


def hero(job_title: str, category: str, location: str) -> None:
    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    st.markdown("<h1>AI Sourcing Assistant</h1>", unsafe_allow_html=True)
    chips = []
    if job_title:
        chips.append("<span class='chip'>🎯 " + job_title + "</span>")
    if category:
        chips.append("<span class='chip'>🧠 " + category.upper() + "</span>")
    if location:
        chips.append("<span class='chip'>📍 " + location + "</span>")
    if chips:
        st.markdown("<div class='chips'>" + "".join(chips) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def code_card(title: str, text: str, hint: str = "") -> None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;font-size:14px;color:var(--muted);'>" + title + "</h3>", unsafe_allow_html=True)
    st.code(text or "", language="text")
    if hint:
        st.markdown("<div class='hint'>" + hint + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ============================ Predictive Suggestions ============================
TITLE_SUGGESTIONS = {
    "software": ["Software Engineer", "Full Stack Engineer", "Backend Engineer", "Frontend Engineer", "Platform Engineer"],
    "machine": ["Machine Learning Engineer", "ML Engineer", "Applied Scientist", "AI Engineer", "Data Scientist"],
    "reliab":  ["Site Reliability Engineer", "SRE", "Platform Reliability Engineer", "DevOps Engineer"],
    "data":    ["Data Engineer", "Analytics Engineer", "Data Platform Engineer"],
    "mobile":  ["iOS Engineer", "Android Engineer", "Mobile Engineer"],
    "security":["Security Engineer", "Application Security Engineer", "Cloud Security Engineer"],
}

COMMON_QUALIFIERS = ["highly scalable", "high throughput", "low latency", "real-time", "cloud-native", "mission critical"]


def suggest_titles(q: str) -> List[str]:
    s = (q or "").lower()
    hits: List[str] = []
    for k, vals in TITLE_SUGGESTIONS.items():
        if k in s:
            for v in vals:
                if v not in hits:
                    hits.append(v)
    if not hits:
        # fallback by category
        cat = map_title_to_category(q or "")
        hits = ROLE_LIB.get(cat, {}).get("titles", [])[:6]
    return hits[:8]


# ============================ UI ============================
# Theme selector (bright only)
col_theme = st.columns([1])[0]
with col_theme:
    theme_choice = st.selectbox("Theme", list(THEMES.keys()), index=0, help="Bright color systems")
inject_css(theme_choice)

# Prominent search input row
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
cA, cB = st.columns([3, 2])
with cA:
    job_title = st.text_input("Search by job title", placeholder="e.g., Senior Machine Learning Engineer")
with cB:
    location = st.text_input("Location (optional)", placeholder="e.g., New York, Remote, Bay Area")

# Predictive title suggestions under the search bar
if job_title and len(job_title) >= 3:
    sugg = suggest_titles(job_title)
    if sugg:
        st.caption("Suggested titles — click to add:")
        btn_cols = st.columns(len(sugg)) if len(sugg) <= 6 else st.columns(6)
        for i, title in enumerate(sugg[:6]):
            if btn_cols[i].button(title, key="sugg_"+str(i)):
                st.session_state["added_title"] = title

extra_not = st.text_input("Extra NOT terms (comma-separated, optional)", placeholder="e.g., contractor, internship")

# Quick filters that influence Keywords only
cf1, cf2, cf3 = st.columns(3)
with cf1:
    level = st.selectbox("Seniority", ["All", "Associate", "Mid", "Senior+", "Staff/Principal"], index=0)
with cf2:
    env = st.selectbox("Work setting", ["Any", "On-site", "Hybrid", "Remote"], index=0)
with cf3:
    size = st.selectbox("Company size focus", ["Any", "Startup", "Growth", "Enterprise"], index=0)

# Build button
build = st.button("✨ Build sourcing pack")

if build and job_title and job_title.strip():
    st.session_state["built"] = True
    st.session_state["role_title"] = job_title
    st.session_state["location"] = location
    st.session_state["category"] = map_title_to_category(job_title)
    R = ROLE_LIB[st.session_state["category"]]
    titles_seed = expand_titles(R["titles"], st.session_state["category"])
    if "added_title" in st.session_state:
        titles_seed = unique_preserve([st.session_state["added_title"]] + titles_seed)
    st.session_state["titles"] = titles_seed
    st.session_state["must"] = list(R["must"])
    st.session_state["nice"] = list(R["nice"])

category = st.session_state.get("category", "")
hero(st.session_state.get("role_title", ""), category, st.session_state.get("location", ""))

if st.session_state.get("built"):
    titles = st.session_state.get("titles", [])
    must = st.session_state.get("must", [])
    nice = st.session_state.get("nice", [])

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Seniority adjustment affects title set for LinkedIn title fields
    titles = apply_seniority(titles, level)

    # Editors (always visible)
    st.subheader("✏️ Customize")
    c1, c2 = st.columns([1, 1])
    with c1:
        newline = chr(10)
        titles_default = newline.join(titles)
        titles_text = st.text_area("Titles (one per line)", value=titles_default, height=150)
    with c2:
        comma_space = chr(44) + chr(32)
        must_default = comma_space.join(must)
        must_text = st.text_area("Must-have skills (comma-separated)", value=must_default, height=120)
        nice_default = comma_space.join(nice)
        nice_text = st.text_area("Nice-to-have skills (comma-separated)", value=nice_default, height=120)

    if st.button("Apply changes"):
        st.session_state["titles"] = [t.strip() for t in titles_text.splitlines() if t.strip()]
        st.session_state["must"] = [s.strip() for s in must_text.split(",") if s.strip()]
        st.session_state["nice"] = [s.strip() for s in nice_text.split(",") if s.strip()]
        titles = st.session_state["titles"]
        must = st.session_state["must"]
        nice = st.session_state["nice"]

    # Qualifiers bias Keywords only
    qual = []
    if env == "Remote":
        qual.append("remote")
    elif env == "Hybrid":
        qual.append("hybrid")
    elif env == "On-site":
        qual.append("on-site")
    if size == "Startup":
        qual.append("startup")
    elif size == "Growth":
        qual.append("scale-up")
    elif size == "Enterprise":
        qual.append("enterprise")
    qual = qual + COMMON_QUALIFIERS[:2]

    # Build LinkedIn-ready strings
    li_title_current = or_group(titles)
    li_title_past = or_group(titles[: min(20, len(titles))])
    extra_not_list = [t.strip() for t in (extra_not or "").split(",") if t.strip()]
    all_not = unique_preserve(SMART_NOT + st.session_state.get("jd_not", []) + extra_not_list)
    li_keywords = build_keywords(must, nice, all_not, qualifiers=qual)
    skills_all_csv = ", ".join(unique_preserve(must + nice))

    # Health & confetti
    issues = string_health_report(li_keywords)
    if issues:
        joiner = chr(10)
        st.warning(joiner.join(["• " + x for x in issues]))
    else:
        st.success("✅ String looks healthy and ready to paste into LinkedIn.")
        st.balloons()

    # Boolean Pack — bright cards
    st.subheader("🎯 Boolean Pack (LinkedIn fields)")
    st.caption("Each block is copyable — paste into the matching LinkedIn field.")
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    code_card("Title (Current) • People → Title (Current)", li_title_current)
    code_card("Title (Past) • People → Title (Past)", li_title_past)
    code_card("Keywords (Boolean) • People → Keywords", li_keywords)
    code_card("Skills (CSV) • People → Skills", skills_all_csv)
    st.markdown("</div>", unsafe_allow_html=True)

    # Export
    st.subheader("⬇️ Export")
    lines: List[str] = []
    lines.append("ROLE: " + st.session_state.get("role_title", ""))
    lines.append("LOCATION: " + (st.session_state.get("location") or ""))
    lines.append("")
    lines.append("TITLE (CURRENT):")
    lines.append(li_title_current)
    lines.append("")
    lines.append("TITLE (PAST):")
    lines.append(li_title_past)
    lines.append("")
    lines.append("KEYWORDS:")
    lines.append(li_keywords)
    lines.append("")
    lines.append("SKILLS (CSV):")
    lines.append(skills_all_csv)
    joiner = chr(10)
    pack_text = joiner.join(lines)
    st.download_button("Download pack (.txt)", data=pack_text, file_name="sourcing_pack.txt")

    # Guidance panel
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.subheader("💡 Pro tips for LinkedIn Recruiter")
    st.markdown("- Put **Title (Current)** and **Title (Past)** into their matching fields.")
    st.markdown("- Put **Keywords** into **People → Keywords** (leave companies empty for broader discovery).")
    st.markdown("- Use **Location** filter separately for geo targeting; this app keeps strings portable.")
    st.markdown("- Trim Keywords if OR count is very high to improve recall & speed.")

else:
    st.info("Type a job title (try 'Staff Machine Learning Engineer') and choose a theme. Then click **Build sourcing pack**.")
