# Ai Sourcing Assistant — Pro Recruiter Toolkit (Streamlit App)

"""
A richer, senior‑recruiter‑friendly sourcing assistant. Given a role preset and (optional) location,
this app now provides:

• Boolean Pack: LinkedIn Title + Keywords, Google X‑ray (copy‑ready), plus Broad vs Focused variants
• Role Intel: must/nice skills, frameworks, clouds, databases, related titles, seniority ladder
• Open‑Source Signals: GitHub + Stack Overflow + Kaggle X‑ray queries (conditional by role)
• Company Maps: top companies, adjacent/feeder companies, and typical team names
• Filters & Exclusions: common false positives, suggested LinkedIn filters, smart NOT template
• Outreach Hooks: value‑prop angles and first‑line starters (skills‑based, non‑demographic)
• Sourcing Checklist: a quick QA before launching a new search

No external APIs; safe for Streamlit Cloud. Ethical sourcing only — focus on skills & experience.
"""

import re
import streamlit as st
from typing import List, Dict

# ----------------------------- Data -----------------------------
ROLE_PRESETS: Dict[str, Dict] = {
    "Software Engineer": {
        "titles": [
            "Software Engineer", "Software Developer", "Full Stack Engineer",
            "Backend Engineer", "Frontend Engineer", "Platform Engineer"
        ],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must_skills": ["python", "java", "javascript", "typescript", "react", "node"],
        "nice_skills": ["go", "aws", "gcp", "azure", "docker", "kubernetes"],
        "frameworks": ["react", "node", "spring", "django", "graphql"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres", "mysql", "redis", "mongodb"],
        "certs": ["AWS Developer", "Azure Developer", "GCP Associate"],
        "false_positives": ["qa tester", "help desk", "desktop support", "sap abap"],
        "top_companies": ["Google", "Amazon", "Meta", "Microsoft", "Netflix", "Stripe", "Airbnb"],
        "adjacent_companies": ["Cloudflare", "Datadog", "Snowflake", "Twilio", "Atlassian"],
        "team_names": ["Platform", "Core Services", "Infrastructure", "Product Engineering"],
    },
    "Machine Learning Engineer": {
        "titles": ["Machine Learning Engineer", "ML Engineer", "AI Engineer", "Applied Scientist"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must_skills": ["python", "pytorch", "tensorflow", "mlops", "docker", "kubernetes"],
        "nice_skills": ["model serving", "ray", "sagemaker", "mlflow", "feature store", "airflow"],
        "frameworks": ["pytorch", "tensorflow", "sklearn", "transformers"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres", "bigquery", "redshift", "snowflake", "feature store"],
        "certs": ["AWS ML Specialty"],
        "false_positives": ["research intern", "bi analyst"],
        "top_companies": ["OpenAI", "DeepMind", "Google", "Amazon AWS AI", "Meta AI", "NVIDIA"],
        "adjacent_companies": ["Cohere", "Anthropic", "Hugging Face", "Scale AI", "Databricks"],
        "team_names": ["Applied AI", "Recommendations", "Search", "ML Platform"],
    },
    "Site Reliability Engineer": {
        "titles": ["Site Reliability Engineer", "SRE", "Reliability Engineer", "Platform Reliability Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must_skills": ["kubernetes", "terraform", "aws", "gcp", "linux", "bash"],
        "nice_skills": ["prometheus", "grafana", "datadog", "pagerduty", "incident response", "helm"],
        "frameworks": ["terraform", "ansible", "helm"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres", "mysql", "redis"],
        "certs": ["CKA", "AWS SysOps"],
        "false_positives": ["desktop support", "network technician"],
        "top_companies": ["Google", "LinkedIn", "Dropbox", "Shopify", "Cloudflare"],
        "adjacent_companies": ["Datadog", "PagerDuty", "Fastly", "Snowflake", "Atlassian"],
        "team_names": ["SRE", "Production Engineering", "Platform", "Reliability"],
    },
}

SMART_EXCLUDE_BASE = [
    "intern", "internship", "fellow", "bootcamp", "student", "professor",
    "sales", "marketing", "hr", "talent acquisition", "recruiter",
    "customer support", "qa tester", "help desk", "desktop support",
]

# --------------------------- Helpers ---------------------------

def or_group(items: List[str]) -> str:
    items = [i for i in items if i]
    return "(" + " OR ".join([f'"{i}"' if " " in i else i for i in items]) + ")"


def build_booleans(titles, must, nice, location: str = "", add_not=True, extra_nots: List[str] = None):
    li_title = or_group(titles)
    li_kw_core = or_group(must + nice)
    nots = SMART_EXCLUDE_BASE + (extra_nots or []) if add_not else []
    li_keywords = f"{li_kw_core} NOT (" + " OR ".join(nots) + ")" if nots else li_kw_core

    site = "site:linkedin.com/in -site:linkedin.com/salary"
    loc = f' "{location}"' if location.strip() else ""
    google_xray = f"{site} {or_group(titles)} {or_group(must + nice)}{loc}".strip()

    # Variant strategies
    broad_kw = or_group(must[:4] + nice[:2])
    focused_kw = or_group(must[:6])
    broad = f"{or_group(titles[:4])} AND {broad_kw}"
    focused = f"{or_group(titles)} AND {focused_kw}"

    return li_title, li_keywords, google_xray, broad, focused


def github_query(skills: List[str]):
    langs = [s for s in skills if s in ["python","javascript","typescript","go","java","c++","rust","kotlin","swift"]]
    if not langs:
        return ""
    return "site:github.com (developer OR engineer) (" + " OR ".join(langs[:6]) + ")"


def stackoverflow_query(skills: List[str]):
    core = (skills[:6] if len(skills) > 0 else [])
    return "site:stackoverflow.com/users (developer OR engineer) (" + " OR ".join(core) + ")"


def kaggle_query(skills: List[str]):
    dl = [s for s in skills if s in ["pytorch","tensorflow","sklearn","xgboost","catboost"]]
    return "site:kaggle.com (Grandmaster OR Master OR Competitions) (" + " OR ".join(dl[:5] or skills[:5]) + ")"


def confidence_score(titles: List[str], must: List[str], nice: List[str]) -> int:
    score = 40 if titles else 20
    score += min(30, len(must) * 5)
    score += min(15, len(nice) * 2)
    if len(titles) > 8 or len(must) + len(nice) > 16:
        score -= 5
    return max(10, min(100, score))

# ----------------------------- Styles -----------------------------
CSS = """
<style>
.card {border:1px solid #e6e6e6; padding:1rem; border-radius:16px; box-shadow:0 1px 2px rgba(0,0,0,.04);}
.badge {display:inline-block; padding:.25rem .6rem; margin:.2rem; border-radius:999px; background:#f1f3f5; font-size:.85rem}
.kicker {color:#6b7280; font-size:.9rem; margin-bottom:.25rem}
.h2 {font-weight:700; font-size:1.25rem; margin:.25rem 0 .5rem}
.small {color:#6b7280; font-size:.85rem}
</style>
"""

st.set_page_config(page_title="Recruiter Sourcing Assistant — Pro", page_icon="🧲", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------ Header ------------------------------
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("<div class='card' style='text-align:center'>🧲</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<div class='kicker'>AI‑forward recruiting utility</div>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Recruiter Sourcing Assistant — Pro Toolkit</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Paste results right into LinkedIn Recruiter, Google, GitHub/StackOverflow/Kaggle X‑rays. No PII, skills‑only sourcing.</div>", unsafe_allow_html=True)

# ----------------------------- Controls -----------------------------
colA, colB, colC = st.columns([2.5, 2, 1])
with colA:
    role_choice = st.selectbox("Role preset", list(ROLE_PRESETS.keys()))
with colB:
    location = st.text_input("Location (optional)", placeholder="e.g., New York, Remote")
with colC:
    use_exclude = st.toggle("Smart NOT", value=True, help="Auto‑exclude interns, recruiters, help desk, etc.")

extra_not = st.text_input("Custom NOT terms (comma‑separated)", placeholder="e.g., contractor, internship")
extra_not_list = [t.strip() for t in extra_not.split(",") if t.strip()]

generate = st.button("✨ Generate sourcing pack", type="primary")

st.divider()

# ------------------------------ Results -----------------------------
if generate:
    P = ROLE_PRESETS[role_choice]
    titles, must, nice = P["titles"], P["must_skills"], P["nice_skills"]

    li_title, li_keywords, google_xray, broad_var, focused_var = build_booleans(
        titles, must, nice, location, use_exclude, P.get("false_positives", []) + extra_not_list
    )
    score = confidence_score(titles, must, nice)

    # Quick metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Titles covered", f"{len(titles)}")
    m2.metric("Skills (must/nice)", f"{len(must)}/{len(nice)}")
    m3.metric("Confidence", f"{score}/100")

    tabs = st.tabs([
        "Boolean Pack", "Role Intel", "Open‑Source Signals", "Company Maps", "Filters & Exclusions", "Outreach Hooks", "Checklist"
    ])

    # --- Tab 1: Boolean Pack ---
    with tabs[0]:
        st.markdown("<div class='kicker'>Copy & paste</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**LinkedIn — Title (Current)**")
            st.code(li_title, language="text")
            st.text_input("Copy Title (Current)", value=li_title, label_visibility="collapsed")
        with c2:
            st.markdown("**LinkedIn — Keywords**")
            st.code(li_keywords, language="text")
            st.text_input("Copy Keywords", value=li_keywords, label_visibility="collapsed")
        st.markdown("**Google X‑ray (LinkedIn)**")
        st.code(google_xray, language="text")
        st.text_input("Copy Google X‑ray", value=google_xray, label_visibility="collapsed")
        st.markdown("**Variant A (Broad)** — use for market mapping")
        st.code(broad_var, language="text")
        st.markdown("**Variant B (Focused)** — use when volume is high")
        st.code(focused_var, language="text")

    # --- Tab 2: Role Intel ---
    with tabs[1]:
        st.markdown("<div class='kicker'>Must‑have skills</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in must]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Nice‑to‑have skills</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in nice]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Frameworks / Stacks</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in P.get("frameworks", [])]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Clouds & Databases</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in P.get("clouds", []) + P.get("databases", [])]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Related titles & seniority ladder</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in P.get("titles", []) + P.get("seniority", [])]), unsafe_allow_html=True)

    # --- Tab 3: Open‑Source Signals ---
    with tabs[2]:
        st.markdown("<div class='kicker'>X‑ray queries for talent discovery</div>", unsafe_allow_html=True)
        gh = github_query(must + nice)
        so = stackoverflow_query(must + nice)
        kg = kaggle_query(must + nice) if "Machine Learning" in role_choice else ""
        if gh:
            st.markdown("**GitHub (developers with relevant repos)**")
            st.code(gh, language="text")
            st.text_input("Copy GitHub X‑ray", value=gh, label_visibility="collapsed")
        if so:
            st.markdown("**Stack Overflow (experienced users)**")
            st.code(so, language="text")
            st.text_input("Copy Stack Overflow X‑ray", value=so, label_visibility="collapsed")
        if kg:
            st.markdown("**Kaggle (ML competitions & profiles)**")
            st.code(kg, language="text")
            st.text_input("Copy Kaggle X‑ray", value=kg, label_visibility="collapsed")
        if not (gh or so or kg):
            st.info("No open‑source recipe needed for this role.")

    # --- Tab 4: Company Maps ---
    with tabs[3]:
        st.markdown("<div class='kicker'>Top companies hiring for this skillset</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='card'>" + " ".join([f"<span class='badge'>{c}</span>" for c in P.get("top_companies", [])]) + "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Adjacent / feeder companies</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='card'>" + " ".join([f"<span class='badge'>{c}</span>" for c in P.get("adjacent_companies", [])]) + "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Typical team names to target</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='card'>" + " ".join([f"<span class='badge'>{c}</span>" for c in P.get("team_names", [])]) + "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Use as include or competitor filters in LinkedIn Recruiter.")

    # --- Tab 5: Filters & Exclusions ---
    with tabs[4]:
        st.markdown("<div class='kicker'>Suggested LinkedIn filters</div>", unsafe_allow_html=True)
        st.markdown(
            """
            - **Title (Current):** paste the Title boolean above
            - **Company:** include Top/Adjacent companies above; exclude current employer if needed
            - **Location:** add your target city/region; widen to country for volume
            - **Years of experience:** 4–10 for Senior SWE/SRE; 3–8 for MLE (adjust to your bar)
            - **Industry (optional):** Cloud/Infra/SaaS for SWE & SRE; AI/ML/SaaS for MLE
            - **Keywords:** paste the Keywords boolean; add/remove frameworks to tune volume
            """
        )
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Common false positives</div>", unsafe_allow_html=True)
        fps = SMART_EXCLUDE_BASE + P.get("false_positives", [])
        st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in fps]), unsafe_allow_html=True)
        st.caption("Use the Smart NOT toggle or paste terms into your NOT group.")

    # --- Tab 6: Outreach Hooks ---
    with tabs[5]:
        st.markdown("<div class='kicker'>Candidate‑centric, skills‑based angles</div>", unsafe_allow_html=True)
        hooks = []
        if "Software Engineer" in role_choice:
            hooks = [
                "Own a core service handling 10k+ rps; modern stack (Go/Java/Python, K8s)",
                "Greenfield feature flag service; autonomy + impact",
                "Path to Staff via platform modernization"
            ]
        if "Machine Learning" in role_choice:
            hooks = [
                "Ship models to prod (LLM/RecSys); real users in weeks, not months",
                "GPU budget + modern tooling (Ray, Triton, MLflow)",
                "Partner with product on measurable lifts (CTR, latency, LTV)"
            ]
        if "Reliability" in role_choice or "SRE" in role_choice:
            hooks = [
                "Own reliability for multi‑region K8s; clear SLOs & error budget policy",
                "Incident program with mature postmortems and time for fixes",
                "Infra roadmap input (capacity, observability, cost)"
            ]
        for h in hooks:
            st.markdown(f"- {h}")
        st.caption("Keep it short; 1 clear CTA for a 15‑min intro. No references to protected characteristics.")

    # --- Tab 7: Checklist ---
    with tabs[6]:
        st.markdown("<div class='kicker'>Pre‑launch QA</div>", unsafe_allow_html=True)
        st.markdown(
            """
            - ✅ Two variants ready (Broad & Focused)
            - ✅ Exclusions set (Smart NOT + custom false positives)
            - ✅ 1–2 frameworks added to tune volume
            - ✅ Company filters (Top + Adjacent) selected
            - ✅ Outreach hook drafted with a measurable impact angle
            - ✅ Saved your best string to reuse for similar roles
            """
        )

else:
    st.info("Pick a role, optionally add a location, add custom NOT terms, then click **Generate sourcing pack**.")
