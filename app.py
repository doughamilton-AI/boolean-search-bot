# app.py
# 🧲 Boolean Search Bot — Simple Mode
# Streamlit app that turns a job title into LinkedIn + Google X-ray booleans.

import re
import streamlit as st
from typing import List, Dict, Tuple

# ---------------------------- PRESETS ----------------------------
# High-success presets for the roles you requested.
PRETRAINED: Dict[str, Dict[str, List[str]]] = {
    # Generic SWE
    "software engineer": {
        "titles": [
            "software engineer", "software developer",
            "full stack engineer", "backend engineer", "frontend engineer"
        ],
        "must": ["python", "java", "javascript", "typescript", "react", "node"],
        "nice": ["go", "golang", "aws", "gcp", "azure", "docker", "kubernetes", "graphql", "postgres", "mysql"],
        "exclude": ["intern", "internship", "fellow", "bootcamp", "student", "professor",
                    "sales", "marketing", "hr", "talent acquisition", "recruiter",
                    "customer support", "qa tester", "junior", "entry level"]
    },
    # Senior SWE (bias to scale/ownership)
    "senior software engineer": {
        "titles": [
            "senior software engineer", "staff software engineer", "lead software engineer",
            "principal software engineer", "senior backend engineer", "senior full stack engineer"
        ],
        "must": ["distributed systems", "microservices", "kubernetes", "docker", "aws", "gcp"],
        "nice": ["golang", "java", "python", "postgres", "kafka", "terraform", "ci/cd"],
        "exclude": ["intern", "internship", "fellow", "bootcamp", "student", "professor",
                    "sales", "marketing", "hr", "talent acquisition", "recruiter",
                    "customer support", "qa tester", "junior", "entry level"]
    },
    # MLE (production focus)
    "machine learning engineer": {
        "titles": ["machine learning engineer", "ml engineer", "mlops engineer", "ai engineer"],
        "must": ["python", "pytorch", "tensorflow", "mlops", "docker", "kubernetes"],
        "nice": ["model serving", "fastapi", "ray", "mlflow", "sagemaker", "feature store", "airflow", "kubeflow"],
        "exclude": ["intern", "internship", "fellow", "bootcamp", "student", "professor",
                    "sales", "marketing", "hr", "talent acquisition", "recruiter",
                    "customer support", "qa tester", "research intern"]
    },
    # SRE (reliability/observability)
    "site reliability engineer": {
        "titles": ["site reliability engineer", "sre", "reliability engineer", "platform reliability engineer"],
        "must": ["kubernetes", "terraform", "aws", "gcp", "linux", "bash"],
        "nice": ["prometheus", "grafana", "datadog", "pagerduty", "incident response",
                 "on-call", "slo", "sla", "sli", "helm"],
        "exclude": ["intern", "internship", "fellow", "bootcamp", "student", "professor",
                    "sales", "marketing", "hr", "talent acquisition", "recruiter",
                    "customer support", "qa tester", "desktop support", "help desk"]
    },
}

# ---------------------------- HELPERS ----------------------------
def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9+#./-]+", text.lower())

def or_group(items: List[str]) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return ""
    if len(items) == 1:
        i = items[0]
        return f"\"{i}\"" if (" " in i or any(ch in i for ch in "+#./-")) else i
    def wrap(x: str) -> str:
        return f"\"{x}\"" if (" " in x or any(ch in x for ch in "+#./-")) else x
    return "(" + " OR ".join(wrap(i) for i in items) + ")"

def not_group(items: List[str]) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return ""
    def wrap(x: str) -> str:
        return f"\"{x}\"" if " " in x else x
    return " NOT (" + " OR ".join(wrap(i) for i in items) + ")"

def build_boolean(titles: List[str], must_skills: List[str], nice_skills: List[str],
                  exclude_terms: List[str], location: str = "") -> Dict[str, str]:
    # LinkedIn
    li_title = or_group(titles)
    li_keywords = " AND ".join([or_group(must_skills + nice_skills), not_group(exclude_terms)]).strip()
    li_keywords = li_keywords.replace(" AND  ", " ").strip()

    # Google X-ray (LinkedIn)
    site_part = "site:linkedin.com/in -site:linkedin.com/salary"
    xr_titles = f" ({' OR '.join([f'\"{t}\"' for t in titles[:6]])})" if titles else ""
    xr_skills = f" ({' OR '.join([f'\"{s}\"' for s in (must_skills + nice_skills)[:8]])})" if (must_skills or nice_skills) else ""
    xr_loc    = f" \"{location}\"" if location else ""
    xr_ex     = f" -({' OR '.join([f'\"{e}\"' for e in exclude_terms[:6]])})" if exclude_terms else ""
    google_xray = f"{site_part}{xr_titles}{xr_skills}{xr_loc}{xr_ex}".strip()

    # GitHub X-ray (optional)
    gh_query = ""
    if any(k in (must_skills + nice_skills) for k in ["python","javascript","typescript","go","java","c++","rust","kotlin","swift"]):
        gh_query = "site:github.com (developer OR engineer) (" \
                   + " OR ".join([s for s in (must_skills + nice_skills)
                                  if s in ["python","javascript","typescript","go","java","c++","rust","kotlin","swift"]][:6]) \
                   + ")"
    return {
        "linkedin_title": li_title,
        "linkedin_keywords": li_keywords,
        "google_xray": google_xray,
        "github_xray": gh_query,
    }

def guess_preset_key(user_title: str) -> str:
    """Very simple mapping: try to match a preset key by substring tokens."""
    t = user_title.lower().strip()
    # Strong checks first
    if "site reliability" in t or "sre" in t:
        return "site reliability engineer"
    if "senior" in t and "software" in t:
        return "senior software engineer"
    if "machine learning" in t or "ml engineer" in t or "ml " in t or t.endswith(" ml"):
        return "machine learning engineer"
    # Generic SWE fallback
    if "software" in t or "developer" in t or "engineer" in t:
        return "software engineer"
    # Final fallback
    return "software engineer"

def confidence_score(titles: List[str], must_skills: List[str], nice_skills: List[str], exclude_terms: List[str]) -> int:
    # Lightweight heuristic (0–100)
    score = 40 if titles else 20
    score += min(30, len(must_skills) * 5)
    score += min(15, len(nice_skills) * 2)
    score += min(10, len([e for e in exclude_terms if e]))
    score = max(10, min(100, score))
    # small penalty for very long ORs
    if len(titles) > 8 or len(must_skills) + len(nice_skills) > 14:
        score = max(10, score - 5)
    return score

# ---------------------------- UI ----------------------------
st.set_page_config(page_title="🧲 Boolean Search Bot (Simple)", page_icon="🧲", layout="wide")
st.title("🧲 Boolean Search Bot — Simple")

st.caption("Type a job title. Get LinkedIn + Google X-ray booleans you can paste into Recruiter and Google.")

col_top = st.columns([2, 1, 1])
with col_top[0]:
    job_title = st.text_input("What role are you sourcing?", placeholder="e.g., Senior Software Engineer")
with col_top[1]:
    location = st.text_input("Location (optional)", placeholder="e.g., New York")
with col_top[2]:
    include_github = st.checkbox("Include GitHub X-ray", value=True)

add_exclusions = st.checkbox("Use smart exclusions", value=True,
                             help="Removes common false positives (intern, recruiter, help desk, etc.).")

if st.button("Generate", type="primary"):
    key = guess_preset_key(job_title or "")
    preset = PRETRAINED[key]
    titles = preset["titles"][:]
    must   = preset["must"][:]
    nice   = preset["nice"][:]
    excludes = preset["exclude"][:] if add_exclusions else []

    strings = build_boolean(titles, must, nice, excludes, location)
    score = confidence_score(titles, must, nice, excludes)

    st.subheader("Results")
    st.metric("SourcerBot confidence", f"{score}/100")
    st.caption("Heuristic based on title coverage, skills breadth, and noise reduction.")

    st.markdown("#### 🔎 LinkedIn Recruiter")
    st.caption("Paste the first line into **Title (Current)** and the second into **Keywords**.")
    c1, c2 = st.columns(2)
    with c1:
        st.code(strings["linkedin_title"], language="text")
        st.text_input("Copy Title (Current)", value=strings["linkedin_title"], label_visibility="collapsed")
    with c2:
        st.code(strings["linkedin_keywords"], language="text")
        st.text_input("Copy Keywords", value=strings["linkedin_keywords"], label_visibility="collapsed")

    st.markdown("#### 🕸️ Google X-ray (LinkedIn)")
    st.code(strings["google_xray"], language="text")
    st.text_input("Copy Google X-ray", value=strings["google_xray"], label_visibility="collapsed")

    if include_github and strings["github_xray"]:
        st.markdown("#### 💻 Google X-ray (GitHub)")
        st.code(strings["github_xray"], language="text")
        st.text_input("Copy GitHub X-ray", value=strings["github_xray"], label_visibility="collapsed")

    st.divider()
    st.caption("Ethical sourcing only — focus on skills and experience; do not target protected characteristics.")
