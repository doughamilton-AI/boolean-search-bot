# AI Sourcing Assistant — Minimal, Stable Build (Reverted to working baseline)
# Streamlit app focused on LinkedIn-ready Boolean strings with JD auto-extract

import re
import json
import streamlit as st

st.set_page_config(page_title="AI Sourcing Assistant", layout="wide")

# ---------------------------- Small Role Library (extensible) ----------------------------
ROLE_LIB = {
    "swe": {
        "titles": [
            "Software Engineer","Software Developer","SDE","SDE I","SDE II","Senior Software Engineer",
            "Full Stack Engineer","Backend Engineer","Frontend Engineer","Platform Engineer"
        ],
        "must": ["python","java","go","microservices","distributed systems"],
        "nice": ["kubernetes","docker","graphql","gRPC","aws"],
    },
    "ml": {
        "titles": [
            "Machine Learning Engineer","ML Engineer","ML Scientist","Applied Scientist",
            "Data Scientist","AI Engineer"
        ],
        "must": ["python","pytorch","tensorflow","mlops","model deployment"],
        "nice": ["sklearn","xgboost","feature store","mlflow","sagemaker"],
    },
    "sre": {
        "titles": [
            "Site Reliability Engineer","SRE","Reliability Engineer","DevOps Engineer","Platform Reliability Engineer"
        ],
        "must": ["kubernetes","terraform","prometheus","grafana","incident response"],
        "nice": ["golang","python","aws","gcp","oncall"],
    },
}

SMART_NOT = [
    "intern","internship","fellow","bootcamp","student","professor",
    "sales","marketing","hr","talent acquisition","recruiter",
    "customer support","help desk","desktop support","qa tester"
]

# ---------------------------- Helpers ----------------------------
def or_group(items):
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return ""
    quoted = [f'"{i}"' if (" " in i and not i.startswith("\"")) else i for i in items]
    return "(" + " OR ".join(quoted) + ")"


def map_title_to_category(t: str) -> str:
    s = (t or "").lower()
    if any(k in s for k in ["reliab","sre","site reliability"]):
        return "sre"
    if any(k in s for k in ["machine learning","ml "," ml","ml-","data scientist","ai engineer"]):
        return "ml"
    return "swe"


def expand_titles(base_titles, cat):
    extra = []
    if cat == "swe":
        extra = ["Software Eng","Software Dev","Full-Stack Engineer","Backend Developer","Frontend Developer"]
    elif cat == "ml":
        extra = ["ML Eng","Machine Learning Specialist","Applied ML Engineer","ML Research Engineer"]
    elif cat == "sre":
        extra = ["Reliability Eng","DevOps SRE","Platform SRE","Production Engineer"]
    seen, out = set(), []
    for t in (base_titles + extra):
        k = t.lower()
        if k not in seen:
            seen.add(k); out.append(t)
    return out


def build_keywords(must, nice, nots):
    core = or_group(must + nice)
    if nots:
        return f"{core} NOT (" + " OR ".join(nots) + ")"
    return core


def jd_extract(jd_text: str):
    """Very light extractor: find frequent known skill tokens across library."""
    jd = (jd_text or "").lower()
    # Global skills pool from libs
    pool = set()
    for role in ROLE_LIB.values():
        for k in (role["must"] + role["nice"]):
            pool.add(k.lower())
    # Tokenize
    tokens = re.findall(r"[a-z0-9+#\.\-]+", jd)
    norm = [t.replace("_"," ") for t in tokens]
    counts = {s: 0 for s in pool}
    for s in pool:
        # simple count by exact token or phrase in text
        counts[s] = jd.count(s)
    ranked = [s for s, c in sorted(counts.items(), key=lambda x: x[1], reverse=True) if c > 0]
    must_ex = ranked[:8]
    nice_ex = ranked[8:16]
    # auto NOT hints
    auto_not = []
    for kw in ["intern","contract","temporary","help desk","desktop support","qa tester","graphic designer"]:
        if kw in jd:
            auto_not.append(kw)
    return must_ex, nice_ex, auto_not

# ---------------------------- UI ----------------------------
st.title("🎯 AI Sourcing Assistant")

colA, colB = st.columns([3,2])
with colA:
    any_title = st.text_input("Job title", placeholder="e.g., Site Reliability Engineer")
with colB:
    location = st.text_input("Location (optional)", placeholder="e.g., San Francisco Bay Area")

extra_not = st.text_input("Extra NOT terms (comma-separated, optional)", placeholder="e.g., contractor, internship")

build = st.button("✨ Build sourcing pack", type="primary")

if build and any_title:
    st.session_state["built"] = True
    st.session_state["role_title"] = any_title
    st.session_state["location"] = location
    st.session_state["category"] = map_title_to_category(any_title)
    # seed editable lists
    R = ROLE_LIB[st.session_state["category"]]
    st.session_state["titles"] = expand_titles(R["titles"], st.session_state["category"])
    st.session_state["must"] = R["must"]
    st.session_state["nice"] = R["nice"]

if st.session_state.get("built"):
    cat = st.session_state["category"]
    titles = st.session_state.get("titles", [])
    must = st.session_state.get("must", [])
    nice = st.session_state.get("nice", [])

    st.subheader("✏️ Customize")
    c1, c2 = st.columns([1,1])
    with c1:
        titles_text = st.text_area("Titles (one per line)", value="
".join(titles), height=150)
    with c2:
        must_text = st.text_area("Must-have skills (comma-separated)", value=", ".join(must), height=120)
        nice_text = st.text_area("Nice-to-have skills (comma-separated)", value=", ".join(nice), height=120)

    apply = st.button("Apply changes")
    if apply:
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
            if m_ex or n_ex or n_not:
                # merge with current
                st.session_state["must"] = list(dict.fromkeys(m_ex or must))
                st.session_state["nice"] = list(dict.fromkeys(n_ex or nice))
                st.session_state["jd_not"] = list(dict.fromkeys(st.session_state.get("jd_not", []) + n_not))
                must = st.session_state["must"]
                nice = st.session_state["nice"]
                st.success(f"Extracted: {len(m_ex)} must, {len(n_ex)} nice, {len(n_not)} NOT terms applied")
            else:
                st.info("No strong matches found in this JD. You can still edit the lists above.")

    # Build LinkedIn-ready strings
    li_title_current = or_group(titles)
    li_title_past = or_group(titles[: min(20, len(titles))])
    extra_not_list = [t.strip() for t in (extra_not or "").split(",") if t.strip()]
    all_not = SMART_NOT + st.session_state.get("jd_not", []) + extra_not_list
    li_keywords = build_keywords(must, nice, all_not)
    skills_all_csv = ", ".join(list(dict.fromkeys(must + nice)))

    st.subheader("🎯 Boolean Pack (LinkedIn fields)")
    st.caption("Each block is copyable — paste into the matching LinkedIn field.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Title (Current)** — Paste into: People → Title (Current)")
        st.code(li_title_current, language="text")
    with col2:
        st.markdown("**Title (Past)** — Paste into: People → Title (Past)")
        st.code(li_title_past, language="text")

    st.markdown("**Keywords (Boolean)** — Paste into: People → Keywords")
    st.code(li_keywords, language="text")

    st.markdown("**Skills (CSV)** — Paste into: People → Skills")
    st.code(skills_all_csv, language="text")

    # Simple string health hints
    issues = []
    if len(li_keywords) > 600:
        issues.append("Keywords look long (>600 chars); consider trimming.")
    if li_keywords.count(" OR ") > 60:
        issues.append("High OR count; consider removing niche or redundant terms.")
    if issues:
        st.warning("
".join([f"• {x}" for x in issues]))
    else:
        st.success("Strings look healthy and ready to paste into LinkedIn.")

else:
    st.info("Type a job title and click **Build sourcing pack**. Then edit titles/skills or paste a JD to auto-extract.")
