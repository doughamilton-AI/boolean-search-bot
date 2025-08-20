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


def build_keywords(must: List[str], nice: List[str], nots: List[str]) -> str:
    core = or_group(unique_preserve(must + nice))
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


# ============================ UI Theming ============================
THEMES = {
    "Electric": {
        "grad": "linear-gradient(135deg, #6366F1 0%, #22D3EE 100%)",
        "bg": "#0B1021",
        "card": "#111827",
        "text": "#E5E7EB",
        "muted": "#9CA3AF",
        "ring": "#8B5CF6"
    },
    "Sunset": {
        "grad": "linear-gradient(135deg, #F97316 0%, #F43F5E 100%)",
        "bg": "#0F0A0A",
        "card": "#1F2937",
        "text": "#F3F4F6",
        "muted": "#D1D5DB",
        "ring": "#FB923C"
    },
    "Aqua": {
        "grad": "linear-gradient(135deg, #06B6D4 0%, #34D399 100%)",
        "bg": "#0A1216",
        "card": "#0F172A",
        "text": "#E2E8F0",
        "muted": "#94A3B8",
        "ring": "#22D3EE"
    },
    "Forest": {
        "grad": "linear-gradient(135deg, #22C55E 0%, #3B82F6 100%)",
        "bg": "#0A100D",
        "card": "#111827",
        "text": "#E5E7EB",
        "muted": "#9CA3AF",
        "ring": "#10B981"
    },
}


def inject_css(theme_name: str, density: str) -> None:
    t = THEMES.get(theme_name, THEMES["Electric"])
    gap = {"Comfortable": "18px", "Cozy": "12px", "Compact": "8px"}.get(density, "12px")
    css = """
    <style>
    :root {
      --grad: """ + t["grad"] + """;
      --bg: """ + t["bg"] + """;
      --card: """ + t["card"] + """;
      --text: """ + t["text"] + """;
      --muted: """ + t["muted"] + """;
      --ring: """ + t["ring"] + """;
      --gap: """ + gap + """;
    }
    .app-bg { background: var(--bg); color: var(--text); }
    .hero {
      padding: 16px 20px; border-radius: 16px; background: var(--card);
      border: 1px solid rgba(255,255,255,.06);
      box-shadow: 0 6px 20px rgba(0,0,0,.35);
    }
    .hero h1 {
      margin: 0; font-size: 28px; font-weight: 800;
      background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
    .chip {
      padding: 6px 10px; border-radius: 999px; font-size: 12px; color: var(--text);
      background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08);
    }
    .grid { display: grid; gap: var(--gap); grid-template-columns: repeat(12, 1fr); }
    .card {
      grid-column: span 6;
      background: var(--card); border: 1px solid rgba(255,255,255,.06); border-radius: 16px;
      padding: 12px 14px; box-shadow: 0 6px 20px rgba(0,0,0,.35);
    }
    .card h3 { margin: 0 0 6px 0; font-size: 14px; color: var(--muted); }
    .hint { font-size: 12px; color: var(--muted); margin-top: 4px; }
    .divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.15), transparent); margin: 8px 0; }
    .pill {
      display:inline-block;padding:4px 10px;border-radius:999px;
      background: var(--grad); color:#0b0f19; font-weight:700; font-size:12px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def hero(job_title: str, category: str, location: str) -> None:
    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    st.markdown("<h1>AI Sourcing Assistant</h1>", unsafe_allow_html=True)
    chips = []
    if job_title:
        chips.append(f"<span class='chip'>🎯 {job_title}</span>")
    if category:
        chips.append(f"<span class='chip'>🧠 {category.upper()}</span>")
    if location:
        chips.append(f"<span class='chip'>📍 {location}</span>")
    if chips:
        st.markdown("<div class='chips'>" + "".join(chips) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def code_card(title: str, text: str, hint: str = "") -> None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
    st.code(text or "", language="text")
    if hint:
        st.markdown(f"<div class='hint'>{hint}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ============================ UI ============================
# Controls row
c_theme, c_density = st.columns([1, 1])
with c_theme:
    theme_choice = st.selectbox("Theme", list(THEMES.keys()), index=0)
with c_density:
    density_choice = st.selectbox("Density", ["Comfortable", "Cozy", "Compact"], index=1)

inject_css(theme_choice, density_choice)

# Input row
cA, cB = st.columns([3, 2])
with cA:
    job_title = st.text_input("Job title", placeholder="e.g., Site Reliability Engineer")
with cB:
    location = st.text_input("Location (optional)", placeholder="e.g., San Francisco Bay Area")

extra_not = st.text_input("Extra NOT terms (comma-separated, optional)", placeholder="e.g., contractor, internship")
build = st.button("✨ Build sourcing pack", type="primary")

if build and job_title and job_title.strip():
    st.session_state["built"] = True
    st.session_state["role_title"] = job_title
    st.session_state["location"] = location
    st.session_state["category"] = map_title_to_category(job_title)
    R = ROLE_LIB[st.session_state["category"]]
    st.session_state["titles"] = expand_titles(R["titles"], st.session_state["category"])
    st.session_state["must"] = list(R["must"])
    st.session_state["nice"] = list(R["nice"])

category = st.session_state.get("category", "")
hero(st.session_state.get("role_title", ""), category, st.session_state.get("location", ""))

if st.session_state.get("built"):
    titles = st.session_state.get("titles", [])
    must = st.session_state.get("must", [])
    nice = st.session_state.get("nice", [])

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
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

    with st.expander("📄 Paste Job Description → Auto-extract", expanded=False):
        jd = st.text_area("Paste JD (optional)", height=160)
        if st.button("Extract from JD"):
            m_ex, n_ex, n_not = jd_extract(jd)
            applied = False
            if m_ex:
                st.session_state["must"] = unique_preserve(m_ex)
                applied = True
            if n_ex:
                st.session_state["nice"] = unique_preserve(n_ex)
                applied = True
            if n_not:
                st.session_state["jd_not"] = unique_preserve(st.session_state.get("jd_not", []) + n_not)
                applied = True
            if applied:
                must = st.session_state["must"]
                nice = st.session_state["nice"]
                st.success("JD extracted and applied.")
            else:
                st.info("No strong matches found — you can still edit the lists above.")

    # Build LinkedIn-ready strings
    li_title_current = or_group(titles)
    li_title_past = or_group(titles[: min(20, len(titles))])
    extra_not_list = [t.strip() for t in (extra_not or "").split(",") if t.strip()]
    all_not = unique_preserve(SMART_NOT + st.session_state.get("jd_not", []) + extra_not_list)
    li_keywords = build_keywords(must, nice, all_not)
    skills_all_csv = ", ".join(unique_preserve(must + nice))

    # Health and confetti
    issues = string_health_report(li_keywords)
    if issues:
        st.warning("\n".join(["• " + x for x in issues]))
    else:
        st.success("✅ String looks healthy and ready to paste into LinkedIn.")
        st.balloons()

    # Boolean Pack — pretty cards
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
    pack_text = "\n".join(lines)
    st.download_button("Download pack (.txt)", data=pack_text, file_name="sourcing_pack.txt")

else:
    st.info("Type a job title and click **Build sourcing pack**. Then edit titles/skills or paste a JD to auto-extract.")
