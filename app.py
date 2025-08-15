# Ai Sourcing Assistant — Enhanced Recruiter Tool (Streamlit App)

"""
Visually‑polished Simple Bot for recruiters. Adds:
• Clean header + layout
• Pretty "chip" tags for skills/titles
• Copy‑friendly fields for each boolean string
• Location‑aware Google X‑ray
• Quick metrics (coverage + confidence)
• Tabs for Results, Keywords/Titles, Companies, Tips

Note: No external APIs; safe for Streamlit Cloud.
"""

import re
import streamlit as st
from typing import List, Dict

# ----------------------------- Data -----------------------------
ROLE_PRESETS: Dict[str, Dict] = {
    "Software Engineer": {
        "titles": ["Software Engineer", "Software Developer", "Full Stack Engineer", "Backend Engineer", "Frontend Engineer"],
        "must_skills": ["python", "java", "javascript", "typescript", "react", "node"],
        "nice_skills": ["go", "aws", "gcp", "azure", "docker", "kubernetes"],
        "top_companies": ["Google", "Amazon", "Meta", "Microsoft", "Netflix", "Stripe", "Airbnb"],
    },
    "Machine Learning Engineer": {
        "titles": ["Machine Learning Engineer", "ML Engineer", "AI Engineer", "Data Scientist"],
        "must_skills": ["python", "pytorch", "tensorflow", "mlops", "docker", "kubernetes"],
        "nice_skills": ["sagemaker", "feature store", "ray", "mlflow", "langchain"],
        "top_companies": ["OpenAI", "DeepMind", "Google", "Amazon AWS AI", "Meta AI", "NVIDIA"],
    },
    "Site Reliability Engineer": {
        "titles": ["Site Reliability Engineer", "SRE", "Reliability Engineer", "Platform Engineer"],
        "must_skills": ["kubernetes", "terraform", "aws", "gcp", "linux", "bash"],
        "nice_skills": ["prometheus", "grafana", "pagerduty", "incident response"],
        "top_companies": ["Google", "LinkedIn", "Dropbox", "Shopify", "Cloudflare"],
    },
}

SMART_EXCLUDE = [
    "intern", "internship", "fellow", "bootcamp", "student", "professor",
    "sales", "marketing", "hr", "talent acquisition", "recruiter",
    "customer support", "qa tester", "help desk", "desktop support",
]

# --------------------------- Helpers ---------------------------

def or_group(items: List[str]) -> str:
    items = [i for i in items if i]
    return "(" + " OR ".join([f'"{i}"' if " " in i else i for i in items]) + ")"


def build_booleans(titles, must, nice, location: str = "", use_exclude=True):
    li_title = or_group(titles)
    li_keywords = or_group(must + nice)
    # Add NOT exclusions to keywords to reduce noise
    if use_exclude:
        li_keywords = f"{li_keywords} NOT (" + " OR ".join(SMART_EXCLUDE) + ")"

    # Google X‑ray for LinkedIn
    site = "site:linkedin.com/in -site:linkedin.com/salary"
    loc = f' "{location}"' if location.strip() else ""
    google_xray = f"{site} {or_group(titles)} {or_group(must + nice)}{loc}".strip()
    return li_title, li_keywords, google_xray


def confidence_score(titles: List[str], must: List[str], nice: List[str]) -> int:
    score = 40 if titles else 20
    score += min(30, len(must) * 5)
    score += min(15, len(nice) * 2)
    if len(titles) > 8 or len(must) + len(nice) > 16:
        score -= 5
    return max(10, min(100, score))

# Simple styling helpers
CSS = """
<style>
.card {border:1px solid #e6e6e6; padding:1rem; border-radius:16px; box-shadow:0 1px 2px rgba(0,0,0,.04);}
.badge {display:inline-block; padding:.25rem .6rem; margin:.2rem; border-radius:999px; background:#f1f3f5; font-size:.85rem}
.kicker {color:#6b7280; font-size:.9rem; margin-bottom:.25rem}
.h2 {font-weight:700; font-size:1.25rem; margin:.25rem 0 .5rem}
.small {color:#6b7280; font-size:.85rem}
</style>
"""

st.set_page_config(page_title="Recruiter Sourcing Assistant", page_icon="🧲", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------ Header ------------------------------
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("<div class='card' style='text-align:center'>🧲</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<div class='kicker'>AI‑forward recruiting utility</div>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Recruiter Sourcing Assistant — Simple Bot</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Paste results right into LinkedIn Recruiter or Google. No PII, skills‑only sourcing.</div>", unsafe_allow_html=True)

# ----------------------------- Controls -----------------------------
colA, colB, colC = st.columns([2.5, 2, 1])
with colA:
    role_choice = st.selectbox("Role preset", list(ROLE_PRESETS.keys()))
with colB:
    location = st.text_input("Location (optional)", placeholder="e.g., New York, Remote")
with colC:
    use_exclude = st.toggle("Smart NOT", value=True, help="Auto‑exclude interns, recruiters, help desk, etc.")

generate = st.button("✨ Generate sourcing pack", type="primary")

st.divider()

# ------------------------------ Results -----------------------------
if generate:
    preset = ROLE_PRESETS[role_choice]
    titles = preset["titles"]
    must = preset["must_skills"]
    nice = preset["nice_skills"]

    li_title, li_keywords, google_xray = build_booleans(titles, must, nice, location, use_exclude)
    score = confidence_score(titles, must, nice)

    # Quick metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Titles covered", f"{len(titles)}")
    m2.metric("Skills (must/nice)", f"{len(must)}/{len(nice)}")
    m3.metric("Confidence", f"{score}/100")

    tabs = st.tabs(["Results", "Keywords & Titles", "Companies", "Tips"])

    # --- Tab 1: Results ---
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

    # --- Tab 2: Keywords & Titles ---
    with tabs[1]:
        st.markdown("<div class='kicker'>Must‑have skills</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in must]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Nice‑to‑have skills</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in nice]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.75rem'>Related titles</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in titles]), unsafe_allow_html=True)

    # --- Tab 3: Companies ---
    with tabs[2]:
        st.markdown("<div class='kicker'>Top companies that hire for this skillset</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='card'>" + " ".join([f"<span class='badge'>{c}</span>" for c in preset["top_companies"]]) + "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Use as include or competitor filters in LinkedIn Recruiter.")

    # --- Tab 4: Tips ---
    with tabs[3]:
        st.markdown("<div class='kicker'>Refinement ideas</div>", unsafe_allow_html=True)
        st.markdown(
            """
            - Start broad, then narrow by adding 1–2 frameworks (e.g., React, Kubernetes).
            - Use **Smart NOT** to remove interns/support roles; add custom NOT terms as needed.
            - Add a city/region to the X‑ray query for localized leads.
            - Run **Variant A (broad)** and **Variant B (focused)** in two tabs and compare results.
            """
        )

else:
    st.info("Pick a role, optionally add a location, then click **Generate sourcing pack**.")
