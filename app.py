# Ai Sourcing Assistant — Pro Recruiter Toolkit (Any Title, Colorful UX, Lean Boolean Pack)

"""
A colorful, senior‑recruiter‑friendly sourcing assistant. Enter **any job title** (e.g.,
"Senior iOS Engineer", "Security Engineer", "Product Designer", "Solutions Architect"),
and get an instant sourcing pack:

• Boolean Pack: LinkedIn Title + Keywords, **Skills (copy‑ready)**, **Extended Titles**, **Expanded Keywords**
• Role Intel: must/nice skills, frameworks, clouds, databases, related titles, seniority ladder
• Signals: conditional X‑rays (GitHub/Stack Overflow/Kaggle/Dribbble/Behance)
• Company Maps: top companies, adjacent/feeder companies, and team names
• Filters & Exclusions: common false positives + Smart NOT + custom NOT terms
• Outreach Hooks: value‑prop angles and first‑line starters (skills‑based only)
• Checklist & Export: pre‑launch QA + one‑click export of the entire pack

No external APIs; safe for Streamlit Cloud. Ethical sourcing only — focus on skills & experience.
"""

import re
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict

# --- Streamlit rerun helper for compatibility across versions ---
def _safe_rerun():
    rr = getattr(st, "rerun", None)
    if callable(rr):
        rr()
    else:
        rr2 = getattr(st, "experimental_rerun", None)
        if callable(rr2):
            rr2()


# ============================= Role Library =============================
# Category‑level presets (used for any job title via fuzzy mapping)
ROLE_LIB: Dict[str, Dict] = {
    "swe": {
        "titles": ["Software Engineer", "Software Developer", "Full Stack Engineer", "Backend Engineer", "Frontend Engineer", "Platform Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["python", "java", "javascript", "typescript", "react", "node"],
        "nice": ["go", "aws", "gcp", "azure", "docker", "kubernetes"],
        "frameworks": ["react", "node", "spring", "django", "graphql"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres", "mysql", "redis", "mongodb"],
        "false_pos": ["qa tester", "help desk", "desktop support", "sap abap"],
        "top_companies": ["Google", "Amazon", "Meta", "Microsoft", "Netflix", "Stripe", "Airbnb"],
        "adjacent": ["Cloudflare", "Datadog", "Snowflake", "Twilio", "Atlassian"],
        "team_names": ["Platform", "Core Services", "Infrastructure", "Product Engineering"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "frontend": {
        "titles": ["Frontend Engineer", "Front End Engineer", "UI Engineer", "Web Engineer", "React Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["javascript", "typescript", "react"],
        "nice": ["next.js", "vue", "graphql", "webpack", "testing library"],
        "frameworks": ["react", "next.js", "vue", "graphql"],
        "clouds": ["aws", "gcp"],
        "databases": ["redis", "postgres"],
        "false_pos": ["webmaster", "wordpress implementer"],
        "top_companies": ["Shopify", "Stripe", "Airbnb", "Netflix", "Canva"],
        "adjacent": ["Vercel", "Figma", "Cloudflare"],
        "team_names": ["Web Platform", "Design Systems", "Growth Web"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "backend": {
        "titles": ["Backend Engineer", "API Engineer", "Distributed Systems Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["java", "go", "python", "microservices", "kubernetes"],
        "nice": ["kafka", "grpc", "terraform"],
        "frameworks": ["spring", "grpc", "django", "fastapi"],
        "clouds": ["aws", "gcp"],
        "databases": ["postgres", "mysql", "redis"],
        "false_pos": ["sharepoint"],
        "top_companies": ["Uber", "Stripe", "Datadog", "Dropbox", "Snowflake"],
        "adjacent": ["Confluent", "Fastly", "Cloudflare"],
        "team_names": ["Core Services", "Messaging", "Compute"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "mobile_ios": {
        "titles": ["iOS Engineer", "iOS Developer", "Mobile iOS Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["swift", "swiftui", "xcode"],
        "nice": ["objective‑c", "combine", "rest", "graphql"],
        "frameworks": ["swiftui", "uikit"],
        "clouds": ["aws", "gcp"],
        "databases": ["realm", "sqlite"],
        "false_pos": ["ios support tech"],
        "top_companies": ["Apple", "Airbnb", "Lyft", "Pinterest"],
        "adjacent": ["Expo", "RevenueCat"],
        "team_names": ["Mobile", "Client", "Apps"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "mobile_android": {
        "titles": ["Android Engineer", "Android Developer", "Mobile Android Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["kotlin", "android sdk", "jetpack"],
        "nice": ["java", "compose", "rest"],
        "frameworks": ["jetpack", "compose"],
        "clouds": ["aws", "gcp"],
        "databases": ["room", "sqlite"],
        "false_pos": ["android support tech"],
        "top_companies": ["Google", "Square", "Cash App", "Uber"],
        "adjacent": ["Expo", "Firebase"],
        "team_names": ["Mobile", "Client", "Apps"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "ml": {
        "titles": ["Machine Learning Engineer", "ML Engineer", "AI Engineer", "Applied Scientist"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["python", "pytorch", "tensorflow", "mlops", "docker", "kubernetes"],
        "nice": ["model serving", "ray", "sagemaker", "mlflow", "feature store", "airflow"],
        "frameworks": ["pytorch", "tensorflow", "sklearn", "transformers"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres", "bigquery", "redshift", "snowflake", "feature store"],
        "false_pos": ["research intern", "bi analyst"],
        "top_companies": ["OpenAI", "DeepMind", "Google", "Amazon AWS AI", "Meta AI", "NVIDIA"],
        "adjacent": ["Cohere", "Anthropic", "Hugging Face", "Scale AI", "Databricks"],
        "team_names": ["Applied AI", "Recommendations", "Search", "ML Platform"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": True, "dribbble": False, "behance": False},
    },
    "data_eng": {
        "titles": ["Data Engineer", "Analytics Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Lead"],
        "must": ["python", "sql", "spark", "airflow"],
        "nice": ["dbt", "kafka", "snowflake", "databricks", "bigquery"],
        "frameworks": ["spark", "dbt", "airflow"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["snowflake", "redshift", "bigquery", "postgres"],
        "false_pos": ["bi analyst"],
        "top_companies": ["Databricks", "Snowflake", "Stripe", "Netflix"],
        "adjacent": ["Fivetran", "Airbyte"],
        "team_names": ["Data Platform", "Data Infra", "Analytics Engineering"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "data_analyst": {
        "titles": ["Data Analyst", "BI Analyst", "Product Analyst"],
        "seniority": ["Junior", "Mid", "Senior"],
        "must": ["sql", "tableau", "looker"],
        "nice": ["python", "dbt", "experimentation", "ab testing"],
        "frameworks": ["tableau", "looker", "mode"],
        "clouds": ["bigquery", "snowflake"],
        "databases": ["snowflake", "redshift", "bigquery"],
        "false_pos": ["financial analyst"],
        "top_companies": ["DoorDash", "Airbnb", "Lyft", "Stripe"],
        "adjacent": ["Mode", "Amplitude"],
        "team_names": ["Product Analytics", "BizOps", "Growth Analytics"],
        "signals": {"github": False, "stackoverflow": False, "kaggle": False, "dribbble": False, "behance": False},
    },
    "pm": {
        "titles": ["Product Manager", "Senior Product Manager", "Group PM", "Principal PM"],
        "seniority": ["Associate", "PM", "Senior", "Principal", "Group"],
        "must": ["roadmap", "prioritization", "analytics", "user research"],
        "nice": ["experimentation", "api", "platform", "ai", "data products"],
        "frameworks": ["jira", "figma", "sql"],
        "clouds": [],
        "databases": [],
        "false_pos": ["project manager (construction)"],
        "top_companies": ["Google", "Amazon", "Meta", "Microsoft"],
        "adjacent": ["Atlassian", "Stripe"],
        "team_names": ["Platform PM", "Core PM", "Growth PM"],
        "signals": {"github": False, "stackoverflow": False, "kaggle": False, "dribbble": False, "behance": False},
    },
    "design": {
        "titles": ["Product Designer", "UX Designer", "UI Designer", "Interaction Designer"],
        "seniority": ["Mid", "Senior", "Lead", "Manager"],
        "must": ["figma", "prototyping", "user research", "design systems"],
        "nice": ["usability testing", "ia", "ux writing"],
        "frameworks": ["figma", "framer"],
        "clouds": [],
        "databases": [],
        "false_pos": ["graphic designer print"],
        "top_companies": ["Figma", "Canva", "Airbnb", "Shopify"],
        "adjacent": ["IDEO", "Pentagram"],
        "team_names": ["Product Design", "UX", "Design Systems"],
        "signals": {"github": False, "stackoverflow": False, "kaggle": False, "dribbble": True, "behance": True},
    },
    "sre": {
        "titles": ["Site Reliability Engineer", "SRE", "Reliability Engineer", "Platform Reliability Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff", "Principal", "Lead"],
        "must": ["kubernetes", "terraform", "aws", "gcp", "linux", "bash"],
        "nice": ["prometheus", "grafana", "datadog", "pagerduty", "incident response", "helm"],
        "frameworks": ["terraform", "ansible", "helm"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres", "mysql", "redis"],
        "false_pos": ["desktop support", "network technician"],
        "top_companies": ["Google", "LinkedIn", "Dropbox", "Shopify", "Cloudflare"],
        "adjacent": ["Datadog", "PagerDuty", "Fastly", "Snowflake", "Atlassian"],
        "team_names": ["SRE", "Production Engineering", "Platform", "Reliability"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "devops": {
        "titles": ["DevOps Engineer", "Platform Engineer", "Infrastructure Engineer"],
        "seniority": ["Junior", "Mid", "Senior", "Staff"],
        "must": ["kubernetes", "terraform", "ci/cd", "aws"],
        "nice": ["gcp", "azure", "ansible", "packer"],
        "frameworks": ["terraform", "argo", "helm"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres"],
        "false_pos": ["it admin"],
        "top_companies": ["Shopify", "Stripe", "Cloudflare", "Datadog"],
        "adjacent": ["HashiCorp", "Pulumi"],
        "team_names": ["Platform", "DevEx", "Infra"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "security": {
        "titles": ["Security Engineer", "AppSec Engineer", "Security Software Engineer"],
        "seniority": ["Mid", "Senior", "Staff", "Principal"],
        "must": ["application security", "threat modeling", "static analysis", "python", "golang"],
        "nice": ["bug bounty", "sast", "dast", "kubernetes"],
        "frameworks": ["owasp", "burp"],
        "clouds": ["aws"],
        "databases": ["postgres"],
        "false_pos": ["soc analyst", "siem operator"],
        "top_companies": ["Google", "Cloudflare", "Stripe", "GitHub"],
        "adjacent": ["Snyk", "Auth0", "Okta"],
        "team_names": ["AppSec", "Product Security", "Platform Security"],
        "signals": {"github": True, "stackoverflow": True, "kaggle": False, "dribbble": False, "behance": False},
    },
    "solutions_arch": {
        "titles": ["Solutions Architect", "Sales Engineer", "Solutions Engineer"],
        "seniority": ["Associate", "Mid", "Senior", "Lead"],
        "must": ["pre‑sales", "proof of concept", "demos", "apis"],
        "nice": ["cloud", "kubernetes", "terraform"],
        "frameworks": ["postman", "terraform"],
        "clouds": ["aws", "gcp", "azure"],
        "databases": ["postgres"],
        "false_pos": ["pure sales rep"],
        "top_companies": ["AWS", "Google Cloud", "Microsoft", "Datadog"],
        "adjacent": ["HashiCorp", "MongoDB"],
        "team_names": ["Solutions", "Sales Engineering", "Field Engineering"],
        "signals": {"github": False, "stackoverflow": False, "kaggle": False, "dribbble": False, "behance": False},
    },
}

SMART_EXCLUDE_BASE = [
    "intern", "internship", "fellow", "bootcamp", "student", "professor",
    "sales", "marketing", "hr", "talent acquisition", "recruiter",
    "customer support", "qa tester", "help desk", "desktop support",
]

# ============================= Helpers =============================

def map_title_to_category(title: str) -> str:
    t = (title or "").lower()
    # Strong keyword checks
    if any(k in t for k in ["sre", "site reliability", "production engineering", "production engineer", "reliability engineer"]):
        return "sre"
    if any(k in t for k in ["ml ", "machine learning", "applied scientist", "llm", "data scientist", "computer vision", "nlp"]):
        return "ml"
    if any(k in t for k in ["data engineer", "analytics engineer", "etl engineer", "data platform"]):
        return "data_eng"
    if any(k in t for k in ["data analyst", "bi analyst", "product analyst", "growth analyst", "business analyst"]):
        return "data_analyst"
    if any(k in t for k in ["frontend", "front end", "ui engineer", "react", "web engineer", "ui developer", "web developer"]):
        return "frontend"
    if any(k in t for k in ["backend", "back end", "distributed systems", "api engineer", "services engineer"]):
        return "backend"
    if any(k in t for k in ["ios", "swift", "iphone"]):
        return "mobile_ios"
    if any(k in t for k in ["android", "kotlin"]):
        return "mobile_android"
    if any(k in t for k in ["devops", "platform engineer", "infrastructure engineer", "cloud engineer", "build engineer", "release engineer"]):
        return "devops"
    if any(k in t for k in ["security engineer", "appsec", "product security", "cloud security", "security architect"]):
        return "security"
    if any(k in t for k in ["solutions architect", "sales engineer", "solutions engineer", "solutions consultant", "customer engineer"]):
        return "solutions_arch"
    if any(k in t for k in ["product manager", "gpm", "principal product manager", "product owner", "tpm", "program manager"]):
        return "pm"
    if any(k in t for k in ["designer", "ux", "ui", "interaction designer", "product designer"]):
        return "design"
    # Generic SWE fallback
    if any(k in t for k in ["engineer", "developer", "software", "programmer", "coder", "full stack", "full-stack", "fullstack"]):
        return "swe"
    # Default to PM as a neutral non‑coding role
    return "pm"


def or_group(items: List[str]) -> str:
    items = [i for i in items if i]
    return "(" + " OR ".join([f'"{i}"' if " " in i else i for i in items]) + ")" if items else ""


def title_abbrevs_for(cat: str) -> List[str]:
    if cat in ["swe", "backend", "frontend", "devops", "sre"]:
        return ["SWE", "Software Eng", "Software Dev", "SDE", "SDE I", "SDE II", "SDE2", "Sr Software Engineer", "Staff Software Engineer", "Principal Software Engineer", "Full-Stack Engineer", "Fullstack Engineer"]
    if cat == "ml":
        return ["ML Engineer", "Machine Learning Eng", "Applied Scientist", "AI Engineer", "Data Scientist", "NLP Engineer", "Computer Vision Engineer"]
    if cat == "data_eng":
        return ["Data Platform Engineer", "Analytics Engineer", "ETL Engineer", "Data Infrastructure Engineer"]
    if cat == "security":
        return ["AppSec Engineer", "Product Security Engineer", "Security Software Engineer", "Cloud Security Engineer"]
    if cat == "design":
        return ["UI/UX Designer", "UX/UI Designer", "Interaction Designer", "Product Designer"]
    if cat == "pm":
        return ["PM", "Sr Product Manager", "Principal PM", "Group PM", "Product Owner", "Technical Program Manager"]
    if cat == "solutions_arch":
        return ["Solutions Architect", "Solutions Engineer", "Sales Engineer", "Customer Engineer", "Solutions Consultant"]
    return []


def expand_titles(base_titles: List[str], cat: str) -> List[str]:
    """Add common abbreviations without changing seniority mix."""
    ext = list(dict.fromkeys(base_titles + title_abbrevs_for(cat)))
    # de‑dupe, keep order
    seen = set()
    out = []
    for x in ext:
        if x.lower() not in seen:
            out.append(x)
            seen.add(x.lower())
    return out


def build_booleans(titles, must, nice, location: str = "", add_not=True, extra_nots: List[str] = None):
    li_title = or_group(titles)
    li_kw_core = or_group(must + nice)
    nots = SMART_EXCLUDE_BASE + (extra_nots or []) if add_not else []
    li_keywords = f"{li_kw_core} NOT (" + " OR ".join(nots) + ")" if nots else li_kw_core

    # Variants kept out of Boolean Pack per UX request
    broad_kw = or_group(must[:4] + nice[:2])
    focused_kw = or_group(must[:6])
    broad = f"{or_group(titles[:4])} AND {broad_kw}"
    focused = f"{or_group(titles)} AND {focused_kw}"

    return li_title, li_keywords, broad, focused


def build_expanded_keywords(must: List[str], nice: List[str], stacks: List[str], clouds: List[str], dbs: List[str]) -> str:
    pool = list(dict.fromkeys(must + nice + stacks + clouds + dbs))
    return or_group(pool[:18])


def confidence_score(titles: List[str], must: List[str], nice: List[str]) -> int:
    score = 40 if titles else 20
    score += min(30, len(must) * 5)
    score += min(15, len(nice) * 2)
    if len(titles) > 12 or len(must) + len(nice) > 20:
        score -= 5
    return max(10, min(100, score))

# -------- Wider‑net fuzzy mapping (no regex in strings to keep deployment simple) --------
from difflib import SequenceMatcher

EXTRA_ALIASES = {
    "swe": ["Software Programmer", "Programmer", "Software Dev", "Full Stack Developer", "Backend Developer", "Frontend Developer", "Platform Software Engineer"],
    "frontend": ["Front-End Engineer", "UI Developer", "Web Developer", "React Developer", "Angular Developer"],
    "backend": ["Back-End Engineer", "API Developer", "Services Engineer", "Platform Backend Engineer"],
    "mobile_ios": ["iOS Software Engineer", "iOS Developer", "iPhone Developer"],
    "mobile_android": ["Android Software Engineer", "Android Developer"],
    "ml": ["ML Scientist", "Machine Learning Scientist", "AI Scientist", "NLP Scientist", "CV Engineer"],
    "data_eng": ["ETL Developer", "Data Pipeline Engineer", "Big Data Engineer", "Data Infrastructure"],
    "data_analyst": ["Growth Analyst", "Product Data Analyst", "BI Developer"],
    "pm": ["Product Owner", "TPM", "Technical Program Manager", "Program Manager"],
    "design": ["UX/UI Designer", "Product Design", "Interaction Designer"],
    "sre": ["Production Engineer", "Reliability Engineer", "DevOps SRE", "Systems Reliability Engineer"],
    "devops": ["Cloud Engineer", "Infrastructure Engineer", "Build Engineer", "Release Engineer", "Platform Engineer (DevOps)"],
    "security": ["Application Security Engineer", "Product Security Engineer", "Cloud Security Engineer"],
    "solutions_arch": ["Solutions Consultant", "Sales Engineer", "Customer Engineer", "Field Engineer"],
}


def _normalize_title(s: str) -> str:
    s = (s or "").lower()
    # strip common seniority tokens
    for w in [" sr ", " senior ", " staff ", " principal ", " lead ", " junior ", " ii ", " iii ", " iv ", " i "]:
        s = s.replace(w, " ")
    # keep only letters and spaces
    cleaned = []
    for ch in s:
        if ch.isalpha() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    s = "".join(cleaned)
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


def _all_aliases_for(cat: str) -> List[str]:
    base = ROLE_LIB.get(cat, {}).get("titles", [])
    return base + title_abbrevs_for(cat) + EXTRA_ALIASES.get(cat, [])


def guess_category_fuzzy(title: str) -> str:
    tnorm = _normalize_title(title)
    best_cat, best_score = None, 0.0
    for cat in ROLE_LIB.keys():
        for alias in _all_aliases_for(cat):
            score = SequenceMatcher(None, tnorm, _normalize_title(alias)).ratio()
            if score > best_score:
                best_score, best_cat = score, cat
    if best_score >= 0.42:
        return best_cat
    # Token overlap fallback
    tokens = set(tnorm.split())
    best_cat2, best_overlap = None, -1
    for cat in ROLE_LIB.keys():
        alias_tokens = set()
        for alias in _all_aliases_for(cat):
            alias_tokens.update(_normalize_title(alias).split())
        overlap = len(tokens & alias_tokens)
        if overlap > best_overlap:
            best_overlap, best_cat2 = overlap, cat
    return best_cat2 or "pm"


def map_title_to_category_any(title: str) -> str:
    primary = map_title_to_category(title)
    if primary == "pm" and title:
        return guess_category_fuzzy(title)
    return primary

# ============================= Theming =============================
PALETTES = {
    "Indigo → Pink": {"bg":"linear-gradient(90deg,#4f46e5,#db2777)", "chip":"#eef2ff", "accent":"#4f46e5"},
    "Emerald → Teal": {"bg":"linear-gradient(90deg,#059669,#14b8a6)", "chip":"#ecfdf5", "accent":"#059669"},
    "Amber → Rose": {"bg":"linear-gradient(90deg,#f59e0b,#f43f5e)", "chip":"#fffbeb", "accent":"#f59e0b"},
}

# ============================= UI =============================
st.set_page_config(page_title="Sourcing Assistant — Any Title", page_icon="🎯", layout="wide")

col_theme, _ = st.columns([1,6])
with col_theme:
    theme_choice = st.selectbox("Theme", list(PALETTES.keys()), index=0)
P = PALETTES[theme_choice]

CSS = f"""
<style>
.header {{
  background: {P['bg']};
  color: white; padding: 18px 22px; border-radius: 18px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
}}
.card {{ border:1px solid #e6e6e6; padding:1rem; border-radius:16px; box-shadow:0 1px 2px rgba(0,0,0,.06); }}
.badge {{ display:inline-block; padding:.25rem .6rem; margin:.2rem; border-radius:999px; background:{P['chip']}; font-size:.85rem }}
.kicker {{ opacity:.9; font-size:.95rem; margin-bottom:.25rem }}
.h2 {{ font-weight:800; font-size:1.35rem; margin:.25rem 0 .5rem }}
.small {{ opacity:.9; font-size:.9rem }}
.primary {{ color:{P['accent']}; font-weight:700 }}
.subcap {{ color:#6b7280; font-size:.9rem; margin-top:.25rem }}
.btncopy {{ background:{P['accent']}; color:white; border:none; border-radius:10px; padding:.35rem .6rem; font-size:.85rem; cursor:pointer; }}
.btncopy:hover {{ opacity:.95 }}
.textarea {{ width:100%; resize:vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; padding:.85rem 1rem; border-radius:12px; border:1px solid #e5e7eb; background:#ffffff; min-height:160px; font-size:15px; line-height:1.45; box-shadow: inset 0 1px 2px rgba(0,0,0,.04); }} 
.textarea:focus {{ outline:none; border-color:#a5b4fc; box-shadow: 0 0 0 3px rgba(99,102,241,.15); }}
.blocktitle {{ font-weight:700; margin-bottom:.4rem }}
.grid {{ display:grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.grid-full {{ display:grid; grid-template-columns: 1fr; gap: 14px; }}
.cardlite {{ border:1px solid #eaeaea; padding:1rem; border-radius:14px; background: linear-gradient(180deg,#ffffff,#f9fafb); box-shadow: 0 6px 18px rgba(0,0,0,.06); }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <div class="kicker">AI‑forward recruiting utility</div>
  <div class="h2">🎯 Sourcing Assistant — Fun, Colorful, and **Any Title**</div>
  <div class="small">Paste results into LinkedIn. Boolean Pack now focuses on **Titles, Keywords, and Skills** for quick copy.</div>
</div>
""", unsafe_allow_html=True)

# ---------- Tiny HTML copy card helper ----------

def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def copy_card(title: str, value: str, key: str, rows_hint: int = 8):
    value = _html_escape(value or "")
    # Bigger, prettier boxes — estimate rows generously
    lines = max(1, len(value.splitlines()))
    ors = value.count(" OR ")
    commas = value.count(",")
    longness = max(lines, (ors // 2) + (commas // 10) + 5)
    est = max(rows_hint, min(20, longness))
    html = f"""
    <div class='cardlite'>
      <div style='display:flex;justify-content:space-between;align-items:center;'>
        <div class='blocktitle'>{title}</div>
        <button class='btncopy' onclick=\"navigator.clipboard.writeText(document.getElementById('{key}').value)\">Copy</button>
      </div>
      <textarea id='{key}' class='textarea' rows='{est}'>{value}</textarea>
    </div>
    """
    # Height: roomier visuals
    components.html(html, height=est * 32 + 120)

st.write("")
colA, colB, colC = st.columns([3,2,2])
with colA:
    any_title = st.text_input("Job title (anything!)", placeholder="e.g., Senior Security Engineer in NYC")
with colB:
    location = st.text_input("Location (optional)", placeholder="e.g., New York, Remote")
with colC:
    # Fallback for older Streamlit versions (some builds don't have st.toggle)
    toggle_widget = getattr(st, "toggle", st.checkbox)
    use_exclude = toggle_widget("Smart NOT", value=True, help="Auto‑exclude interns, recruiters, help desk, etc.")
    if not hasattr(st, "toggle"):
        st.caption("Using checkbox fallback — upgrade Streamlit to enable the toggle UI.")

extra_not = st.text_input("Custom NOT terms (comma‑separated)", placeholder="e.g., contractor, internship")
extra_not_list = [t.strip() for t in extra_not.split(",") if t.strip()]

build_clicked = st.button("✨ Build sourcing pack", type="primary")
if build_clicked:
    # Persist a baseline so edits survive reruns
    cat_tmp = map_title_to_category_any(any_title)
    st.session_state["built"] = True
    st.session_state["cat"] = cat_tmp
    st.session_state["any_title"] = any_title
    st.session_state["location"] = location
    st.session_state["use_exclude"] = use_exclude
    # Seed editable lists from the role library
    R0 = ROLE_LIB[cat_tmp]
    st.session_state["edited_titles"] = expand_titles(R0["titles"], cat_tmp)
    st.session_state["edited_must"] = R0["must"]
    st.session_state["edited_nice"] = R0["nice"]
    st.session_state["selected_extras"] = []  # frameworks/clouds/dbs to optionally add to Core
    st.session_state["include_extras_core"] = False
    _safe_rerun()

if st.session_state.get("built"):
    # ===== Rebuild strings from current (possibly edited) lists =====
    cat = st.session_state.get("cat")
    R = ROLE_LIB[cat]

    # Live lists (editable)
    titles = st.session_state.get("edited_titles", expand_titles(R["titles"], cat))
    must = st.session_state.get("edited_must", R["must"])
    nice = st.session_state.get("edited_nice", R["nice"])

    # Extras to widen/narrow volume
    extras_options = list(dict.fromkeys(R.get("frameworks", []) + R.get("clouds", []) + R.get("databases", [])))
    selected_extras = st.session_state.get("selected_extras", [])
    include_extras_core = st.session_state.get("include_extras_core", False)

    # Build strings (respect Smart NOT + custom NOT on every run)
    # Title
    li_title = or_group(titles)
    # Keywords (Core)
    core_terms = must + nice + (selected_extras if include_extras_core else [])
    li_kw_core = or_group(core_terms)
    nots = SMART_EXCLUDE_BASE + R.get("false_pos", []) + [t.strip() for t in (extra_not or "").split(",") if t.strip()]
    li_keywords = f"{li_kw_core} NOT (" + " OR ".join(nots) + ")" if nots else li_kw_core

    # Expanded keywords stay broad (full stack + clouds + dbs)
    expanded_keywords = build_expanded_keywords(must, nice, R.get("frameworks", []), R.get("clouds", []), R.get("databases", []))

    # CSV skills for LinkedIn Skills filter
    skills_must_csv = ", ".join(must)
    skills_nice_csv = ", ".join(nice)
    skills_all_csv = ", ".join(list(dict.fromkeys(must + nice)))

    score = confidence_score(titles, must, nice)

    m1, m2, m3 = st.columns(3)
    m1.metric("Titles covered", f"{len(titles)}")
    m2.metric("Skills (must/nice)", f"{len(must)}/{len(nice)}")
    m3.metric("Confidence", f"{score}/100")

    tabs = st.tabs([
        "🎯 Boolean Pack", "🧠 Role Intel", "🌐 Signals", "🏢 Company Maps", "🚦 Filters", "💌 Outreach", "✅ Checklist", "⬇️ Export"
    ])

    # -------------------- Tab 1: Boolean Pack (Titles, Keywords, Skills only) --------------------
    with tabs[0]:
        # ---- Inline editors & chips (Customize) ----
        with st.expander("✏️ Customize titles & skills (live)", expanded=False):
            col_ed1, col_ed2 = st.columns([1,1])
            with col_ed1:
                titles_text = st.text_area("Titles (one per line)", value="\n".join(titles), height=180)
            with col_ed2:
                must_text = st.text_area("Must-have skills (comma-separated)", value=", ".join(must), height=120)
                nice_text = st.text_area("Nice-to-have skills (comma-separated)", value=", ".join(nice), height=120)
            col_chip1, col_chip2 = st.columns([1,1])
            with col_chip1:
                selected_extras_new = st.multiselect("Optional extras (frameworks/clouds/dbs)", options=extras_options, default=selected_extras)
            with col_chip2:
                include_extras_core_new = st.checkbox("Include selected extras in Core Keywords", value=include_extras_core)
            if st.button("Apply changes", key="apply_edits"):
                st.session_state["edited_titles"] = [t.strip() for t in titles_text.splitlines() if t.strip()]
                st.session_state["edited_must"] = [s.strip() for s in must_text.split(",") if s.strip()]
                st.session_state["edited_nice"] = [s.strip() for s in nice_text.split(",") if s.strip()]
                st.session_state["selected_extras"] = selected_extras_new
                st.session_state["include_extras_core"] = include_extras_core_new
                _safe_rerun()

        # ---- Copy cards ----
        ext_title = or_group(titles[:20])
        grid1 = st.container()
        with grid1:
            st.markdown("<div class='grid'>", unsafe_allow_html=True)
            copy_card("LinkedIn — Title (Current)", li_title, "copy_title_current", 10)
            copy_card("LinkedIn — Title (Current) — Extended synonyms", ext_title, "copy_title_extended", 10)
            st.markdown("</div>", unsafe_allow_html=True)

        grid2 = st.container()
        with grid2:
            st.markdown("<div class='grid'>", unsafe_allow_html=True)
            copy_card("LinkedIn — Keywords (Core)", li_keywords, "copy_kw_core", 12)
            copy_card("LinkedIn — Keywords (Expanded)", expanded_keywords, "copy_kw_expanded", 12)
            st.markdown("</div>", unsafe_allow_html=True)

        grid3 = st.container()
        with grid3:
            st.markdown("<div class='grid'>", unsafe_allow_html=True)
            copy_card("LinkedIn — Skills (Must, CSV)", skills_must_csv, "copy_sk_must", 8)
            copy_card("LinkedIn — Skills (Nice‑to‑have, CSV)", skills_nice_csv, "copy_sk_nice", 8)
            st.markdown("</div>", unsafe_allow_html=True)

        grid4 = st.container()
        with grid4:
            st.markdown("<div class='grid-full'>", unsafe_allow_html=True)
            copy_card("LinkedIn — Skills (All, CSV)", skills_all_csv, "copy_sk_all", 10)
            st.markdown("</div>", unsafe_allow_html=True)

        # ---- Copy All bundle ----
        copy_all = f"""Title (Current):
{li_title}

Title (Extended):
{ext_title}

Keywords (Core):
{li_keywords}

Keywords (Expanded):
{expanded_keywords}

Skills (All CSV):
{skills_all_csv}
"""
        st.markdown("<div class='grid-full'>", unsafe_allow_html=True)
        copy_card("Copy All — Titles + Keywords + Skills", copy_all, "copy_all_bundle", 14)
        st.markdown("</div>", unsafe_allow_html=True)

        # ---- 🧪 String Health ----
        def _paren_ok(s: str) -> bool:
            depth = 0
            for ch in s:
                if ch == '(': depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth < 0: return False
            return depth == 0
        def _terms_from_or_group(g: str):
            g = g.strip()
            if g.startswith('(') and g.endswith(')'):
                g = g[1:-1]
            parts = [p.strip().strip('"').lower() for p in g.split(' OR ') if p.strip()]
            seen, dups = set(), set()
            for p in parts:
                if p in seen: dups.add(p)
                else: seen.add(p)
            return parts, dups
        core_part = li_keywords.split(" NOT ")[0].strip()
        title_terms, title_dups = _terms_from_or_group(li_title)
        core_terms_list, core_dups = _terms_from_or_group(core_part)
        health_cols = st.columns(4)
        health_cols[0].metric("Chars (Keywords)", len(li_keywords))
        health_cols[1].metric("OR count", li_keywords.count(" OR "))
        health_cols[2].metric("Title terms", len(title_terms))
        health_cols[3].metric("Dupes in Core", len(core_dups))
        issues = []
        if len(li_keywords) > 500: issues.append("Keywords are long; consider trimming to < 500 chars")
        if li_keywords.count(" OR ") > 60: issues.append("High OR count; remove niche or redundant terms")
        if not _paren_ok(li_keywords): issues.append("Unbalanced parentheses; copy fresh from cards")
        if core_dups: issues.append("Duplicate core terms: " + ", ".join(sorted(core_dups)))
        if issues:
            st.warning("\n".join([f"• {x}" for x in issues]))
        else:
            st.success("String looks healthy and ready to paste into LinkedIn.")

    # -------------------- Tab 2: Role Intel --------------------
    with tabs[1]:
        st.markdown("<span class='kicker'>Must‑have</span>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in must]), unsafe_allow_html=True)
        st.markdown("<span class='kicker' style='margin-top:.6rem'>Nice‑to‑have</span>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in nice]), unsafe_allow_html=True)
        st.markdown("<span class='kicker' style='margin-top:.6rem'>Frameworks/Stacks</span>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in R.get("frameworks", [])]), unsafe_allow_html=True)
        st.markdown("<span class='kicker' style='margin-top:.6rem'>Clouds & Databases</span>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{s}</span>" for s in R.get("clouds", []) + R.get("databases", [])]), unsafe_allow_html=True)
        st.markdown("<span class='kicker' style='margin-top:.6rem'>Related titles & seniority</span>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in R.get("titles", []) + R.get("seniority", [])]), unsafe_allow_html=True)

    # -------------------- Tab 3: Signals --------------------
    with tabs[2]:
        sig = R.get("signals", {})
        if sig.get("github"):
            gh = "site:github.com (developer OR engineer) (" + " OR ".join([s for s in (must + nice) if s in ["python","javascript","typescript","go","java","c++","rust","kotlin","swift"]][:6]) + ")"
            if gh:
                st.markdown("**GitHub**")
                st.code(gh, language="text")
                st.text_input("Copy GitHub X‑ray", value=gh, label_visibility="collapsed")
        if sig.get("stackoverflow"):
            so = "site:stackoverflow.com/users (developer OR engineer) (" + " OR ".join((must + nice)[:6]) + ")"
            st.markdown("**Stack Overflow**")
            st.code(so, language="text")
            st.text_input("Copy Stack Overflow X‑ray", value=so, label_visibility="collapsed")
        if sig.get("kaggle"):
            kg = "site:kaggle.com (Grandmaster OR Master OR Competitions) (" + " OR ".join([s for s in (must + nice) if s in ["pytorch","tensorflow","sklearn","xgboost","catboost"]][:5] or (must + nice)[:5]) + ")"
            st.markdown("**Kaggle**")
            st.code(kg, language="text")
            st.text_input("Copy Kaggle X‑ray", value=kg, label_visibility="collapsed")
        if sig.get("dribbble"):
            db = "site:dribbble.com (Product Designer OR UX OR UI) (Figma OR prototype OR case study)"
            st.markdown("**Dribbble**")
            st.code(db, language="text")
            st.text_input("Copy Dribbble X‑ray", value=db, label_visibility="collapsed")
        if sig.get("behance"):
            be = "site:behance.net (Product Design OR UX) (Figma OR prototype OR case study)"
            st.markdown("**Behance**")
            st.code(be, language="text")
            st.text_input("Copy Behance X‑ray", value=be, label_visibility="collapsed")

    # -------------------- Tab 4: Company Maps --------------------
    with tabs[3]:
        st.markdown("<div class='kicker'>Top companies</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{c}</span>" for c in R.get("top_companies", [])]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.6rem'>Adjacent / feeder companies</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{c}</span>" for c in R.get("adjacent", [])]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.6rem'>Team names to target</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{c}</span>" for c in R.get("team_names", [])]), unsafe_allow_html=True)

    # -------------------- Tab 5: Filters --------------------
    with tabs[4]:
        st.markdown("""
        **LinkedIn tips**
        - **Title (Current):** use the Title boolean (standard first; extended if low volume)
        - **Company:** include Top/Adjacent; exclude current employer if needed
        - **Location:** add city/region; widen to country if volume is low
        - **Experience:** pick a realistic band for the role’s level
        - **Keywords:** use Core; try Expanded when targeting specific stacks
        """)
        fps = SMART_EXCLUDE_BASE + R.get("false_pos", []) + [t.strip() for t in (extra_not or "").split(",") if t.strip()]
        st.markdown("<div class='kicker' style='margin-top:.6rem'>Common NOT terms</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in fps]), unsafe_allow_html=True)

    # -------------------- Tab 6: Outreach --------------------
    with tabs[5]:
        st.markdown("**Angles that resonate** (keep 1 short CTA)")
        hooks = []
        cat_icons = {"swe":"🧱","frontend":"🎨","backend":"🧩","mobile_ios":"📱","mobile_android":"🤖","ml":"🧪","data_eng":"🗄️","data_analyst":"📊","pm":"🧭","design":"✏️","sre":"🚦","devops":"⚙️","security":"🛡️","solutions_arch":"🧰"}
        icon = cat_icons.get(cat, "✨")
        if cat in ["swe","backend","frontend","devops","sre"]:
            hooks = [
                "Own a core service at scale; modern stack (K8s/Cloud)",
                "Greenfield feature with autonomy & measurable impact",
            ]
        elif cat == "ml":
            hooks = [
                "Ship models to prod fast (LLM/RecSys)",
                "GPU budget + modern tooling (Ray/MLflow)",
            ]
        elif cat == "data_eng":
            hooks = [
                "Modern data stack (Spark/DBT/Snowflake)",
                "Own pipelines that unblock product teams",
            ]
        elif cat == "data_analyst":
            hooks = [
                "Partner with PMs on experiment design",
                "Direct line from analysis → product decisions",
            ]
        elif cat == "design":
            hooks = [
                "Own product surfaces + contribute to design system",
                "Tight research → prototype → ship loop with measurable outcomes",
            ]
        elif cat == "pm":
            hooks = [
                "High‑leverage platform surface area",
                "Clear metrics ownership (activation/retention)",
            ]
        elif cat == "security":
            hooks = [
                "Own AppSec roadmap and threat modeling",
                "Time/budget for fixing systemic security issues",
            ]
        elif cat == "solutions_arch":
            hooks = [
                "Complex, technical pre‑sales with real engineering",
                "Autonomy over POCs and customer outcomes",
            ]
        for h in hooks:
            st.markdown(f"- {icon} {h}")

    # -------------------- Tab 7: Checklist --------------------
    with tabs[6]:
        st.markdown("""
        - ✅ Broad & Focused variants ready
        - ✅ NOT terms set (Smart + custom)
        - ✅ 1–2 frameworks toggled for volume control
        - ✅ Company filters selected (Top + Adjacent)
        - ✅ Outreach angle drafted with measurable impact
        - ✅ Save the best string for reuse on similar roles
        """)

    # -------------------- Tab 8: Export --------------------
    with tabs[7]:
        pack = f"""
ROLE: {st.session_state.get('any_title','')}
LOCATION: {st.session_state.get('location','N/A') or 'N/A'}
CONFIDENCE: {score}/100

TITLES: {', '.join(titles)}
MUST: {', '.join(must)}
NICE: {', '.join(nice)}

LINKEDIN TITLE:
{li_title}

EXTENDED TITLE:
{or_group(titles[:20])}

KEYWORDS (CORE):
{li_keywords}

KEYWORDS (EXPANDED):
{expanded_keywords}

SKILLS (MUST):
{skills_must_csv}

SKILLS (NICE):
{skills_nice_csv}

SKILLS (ALL):
{skills_all_csv}
        """
        st.download_button("Download pack (.txt)", data=pack, file_name="sourcing_pack.txt")
else:
    st.info("Type **any job title**, optionally add a location and custom NOT terms, then click **Build sourcing pack**.")

