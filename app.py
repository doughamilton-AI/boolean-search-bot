# Ai Sourcing Assistant — Pro Recruiter Toolkit (Any Title, Colorful UX)

"""
A colorful, senior‑recruiter‑friendly sourcing assistant. Enter **any job title** (e.g.,
"Senior iOS Engineer", "Security Engineer", "Product Designer", "Solutions Architect"),
and get an instant sourcing pack:

• Boolean Pack: LinkedIn Title + Keywords, Google X‑ray, plus Broad vs Focused variants
• Role Intel: must/nice skills, frameworks, clouds, databases, related titles, seniority ladder
• Signals: conditional X‑rays (GitHub/Stack Overflow/Kaggle/Dribbble/Behance)
• Company Maps: top companies, adjacent/feeder companies, and team names
• Filters & Exclusions: common false positives + Smart NOT + custom NOT terms
• Outreach Hooks: value‑prop angles and first‑line starters (skills‑based only)
• Checklist & Export: pre‑launch QA + one‑click export of the entire pack

No external APIs; safe for Streamlit Cloud. Ethical sourcing only — focus on skills & experience.
"""

import re
import textwrap
import streamlit as st
from typing import List, Dict

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
        "certs": ["AWS Developer", "Azure Developer", "GCP Associate"],
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
        "certs": [],
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
        "certs": [],
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
        "certs": [],
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
        "certs": [],
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
        "certs": ["AWS ML Specialty"],
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
        "certs": [],
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
        "certs": [],
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
        "certs": [],
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
        "certs": [],
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
        "certs": ["CKA", "AWS SysOps"],
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
        "certs": [],
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
        "certs": ["OSCP", "CISSP"],
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
        "certs": ["AWS SA‑Associate"],
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

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9+#./-]+", text.lower())


def map_title_to_category(title: str) -> str:
    t = (title or "").lower()
    # Strong keyword checks
    if any(k in t for k in ["sre", "site reliability", "production engineering"]):
        return "sre"
    if any(k in t for k in ["ml ", "machine learning", "applied scientist", "llm"]):
        return "ml"
    if any(k in t for k in ["data engineer", "analytics engineer"]):
        return "data_eng"
    if any(k in t for k in ["data analyst", "bi analyst", "product analyst"]):
        return "data_analyst"
    if any(k in t for k in ["frontend", "front end", "ui engineer", "react"]):
        return "frontend"
    if any(k in t for k in ["backend", "distributed systems", "api engineer"]):
        return "backend"
    if any(k in t for k in ["ios", "swift"]):
        return "mobile_ios"
    if any(k in t for k in ["android", "kotlin"]):
        return "mobile_android"
    if any(k in t for k in ["devops", "platform engineer", "infrastructure engineer"]):
        return "devops"
    if any(k in t for k in ["security engineer", "appsec", "product security"]):
        return "security"
    if any(k in t for k in ["solutions architect", "sales engineer", "solutions engineer"]):
        return "solutions_arch"
    if any(k in t for k in ["product manager", "gpm", "principal product manager"]):
        return "pm"
    if any(k in t for k in ["designer", "ux", "ui", "interaction designer"]):
        return "design"
    # Generic SWE fallback
    if any(k in t for k in ["engineer", "developer", "software"]):
        return "swe"
    # Default to PM as a neutral non‑coding role
    return "pm"


def or_group(items: List[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    return "(" + " OR ".join([f'"{i}"' if " " in i else i for i in items]) + ")"


def build_booleans(titles, must, nice, location: str = "", add_not=True, extra_nots: List[str] = None):
    li_title = or_group(titles)
    li_kw_core = or_group(must + nice)
    nots = SMART_EXCLUDE_BASE + (extra_nots or []) if add_not else []
    li_keywords = f"{li_kw_core} NOT (" + " OR ".join(nots) + ")" if nots else li_kw_core

    site = "site:linkedin.com/in -site:linkedin.com/salary"
    loc = f' "{location}"' if location.strip() else ""
    google_xray = f"{site} {or_group(titles)} {or_group(must + nice)}{loc}".strip()

    # Variants
    broad_kw = or_group(must[:4] + nice[:2])
    focused_kw = or_group(must[:6])
    broad = f"{or_group(titles[:4])} AND {broad_kw}"
    focused = f"{or_group(titles)} AND {focused_kw}"

    return li_title, li_keywords, google_xray, broad, focused


def confidence_score(titles: List[str], must: List[str], nice: List[str]) -> int:
    score = 40 if titles else 20
    score += min(30, len(must) * 5)
    score += min(15, len(nice) * 2)
    if len(titles) > 8 or len(must) + len(nice) > 16:
        score -= 5
    return max(10, min(100, score))

# Signal queries

def github_query(skills: List[str]):
    langs = [s for s in skills if s in ["python","javascript","typescript","go","java","c++","rust","kotlin","swift"]]
    return ("site:github.com (developer OR engineer) (" + " OR ".join(langs[:6]) + ")") if langs else ""

def stackoverflow_query(skills: List[str]):
    core = (skills[:6] if len(skills) > 0 else [])
    return ("site:stackoverflow.com/users (developer OR engineer) (" + " OR ".join(core) + ")") if core else ""

def kaggle_query(skills: List[str]):
    dl = [s for s in skills if s in ["pytorch","tensorflow","sklearn","xgboost","catboost"]]
    return ("site:kaggle.com (Grandmaster OR Master OR Competitions) (" + " OR ".join(dl[:5] or skills[:5]) + ")") if (dl or skills) else ""

def dribbble_query(skills: List[str]):
    return "site:dribbble.com (Product Designer OR UX OR UI) (Figma OR prototype OR case study)"

def behance_query(skills: List[str]):
    return "site:behance.net (Product Design OR UX) (Figma OR prototype OR case study)"

# ============================= Theming =============================
PALETTES = {
    "Indigo → Pink": {"bg":"linear-gradient(90deg,#4f46e5,#db2777)", "chip":"#eef2ff", "accent":"#4f46e5"},
    "Emerald → Teal": {"bg":"linear-gradient(90deg,#059669,#14b8a6)", "chip":"#ecfdf5", "accent":"#059669"},
    "Amber → Rose": {"bg":"linear-gradient(90deg,#f59e0b,#f43f5e)", "chip":"#fffbeb", "accent":"#f59e0b"},
}

# ============================= UI =============================
st.set_page_config(page_title="Sourcing Assistant — Any Title", page_icon="🎯", layout="wide")

# Controls up top to theme the page
col_theme, col_title = st.columns([1,6])
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
.card {{border:1px solid #e6e6e6; padding:1rem; border-radius:16px; box-shadow:0 1px 2px rgba(0,0,0,.06);}}
.badge {{display:inline-block; padding:.25rem .6rem; margin:.2rem; border-radius:999px; background:{P['chip']}; font-size:.85rem}}
.kicker {{opacity:.9; font-size:.95rem; margin-bottom:.25rem}}
.h2 {{font-weight:800; font-size:1.35rem; margin:.25rem 0 .5rem}}
.small {{opacity:.9; font-size:.9rem}}
.primary {{color:{P['accent']}; font-weight:700}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div class="header">
  <div class="kicker">AI‑forward recruiting utility</div>
  <div class="h2">🎯 Sourcing Assistant — Fun, Colorful, and **Any Title**</div>
  <div class="small">Paste results into LinkedIn, Google, and community sites. Skills‑only, ethical sourcing.</div>
</div>
""", unsafe_allow_html=True)

st.write("")
colA, colB, colC = st.columns([3,2,2])
with colA:
    any_title = st.text_input("Job title (anything!)", placeholder="e.g., Senior Security Engineer in NYC")
with colB:
    location = st.text_input("Location (optional)", placeholder="e.g., New York, Remote")
with colC:
    use_exclude = st.toggle("Smart NOT", value=True)

extra_not = st.text_input("Custom NOT terms (comma‑separated)", placeholder="e.g., contractor, internship")
extra_not_list = [t.strip() for t in extra_not.split(",") if t.strip()]

if st.button("✨ Build sourcing pack", type="primary"):
    cat = map_title_to_category(any_title)
    R = ROLE_LIB[cat]

    titles = R["titles"]
    must = R["must"]
    nice = R["nice"]

    li_title, li_keywords, google_xray, broad_var, focused_var = build_booleans(
        titles, must, nice, location, use_exclude, R.get("false_pos", []) + extra_not_list
    )
    score = confidence_score(titles, must, nice)

    # fun confetti
    st.balloons()

    m1, m2, m3 = st.columns(3)
    m1.metric("Titles covered", f"{len(titles)}")
    m2.metric("Skills (must/nice)", f"{len(must)}/{len(nice)}")
    m3.metric("Confidence", f"{score}/100")

    tabs = st.tabs([
        "🎯 Boolean Pack", "🧠 Role Intel", "🌐 Signals", "🏢 Company Maps", "🚦 Filters", "💌 Outreach", "✅ Checklist", "⬇️ Export"
    ])

    # Boolean Pack
    with tabs[0]:
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
        st.markdown("**Variant A (Broad)**")
        st.code(broad_var, language="text")
        st.markdown("**Variant B (Focused)**")
        st.code(focused_var, language="text")

    # Role Intel
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

    # Signals (Open‑source or portfolio sites)
    with tabs[2]:
        sig = R.get("signals", {})
        if sig.get("github"):
            gh = github_query(must + nice)
            if gh:
                st.markdown("**GitHub**")
                st.code(gh, language="text")
                st.text_input("Copy GitHub X‑ray", value=gh, label_visibility="collapsed")
        if sig.get("stackoverflow"):
            so = stackoverflow_query(must + nice)
            if so:
                st.markdown("**Stack Overflow**")
                st.code(so, language="text")
                st.text_input("Copy Stack Overflow X‑ray", value=so, label_visibility="collapsed")
        if sig.get("kaggle"):
            kg = kaggle_query(must + nice)
            if kg:
                st.markdown("**Kaggle**")
                st.code(kg, language="text")
                st.text_input("Copy Kaggle X‑ray", value=kg, label_visibility="collapsed")
        if sig.get("dribbble"):
            db = dribbble_query(must + nice)
            st.markdown("**Dribbble**")
            st.code(db, language="text")
            st.text_input("Copy Dribbble X‑ray", value=db, label_visibility="collapsed")
        if sig.get("behance"):
            be = behance_query(must + nice)
            st.markdown("**Behance**")
            st.code(be, language="text")
            st.text_input("Copy Behance X‑ray", value=be, label_visibility="collapsed")
        if not any(sig.values()):
            st.info("No external signal recipe for this role.")

    # Company Maps
    with tabs[3]:
        st.markdown("<div class='kicker'>Top companies</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{c}</span>" for c in R.get("top_companies", [])]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.6rem'>Adjacent / feeder companies</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{c}</span>" for c in R.get("adjacent", [])]), unsafe_allow_html=True)
        st.markdown("<div class='kicker' style='margin-top:.6rem'>Team names to target</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{c}</span>" for c in R.get("team_names", [])]), unsafe_allow_html=True)

    # Filters
    with tabs[4]:
        st.markdown("""
        **LinkedIn tips**
        - **Title (Current):** use the Title boolean
        - **Company:** include Top/Adjacent; exclude current employer if needed
        - **Location:** add city/region; widen to country if volume is low
        - **Experience:** pick a realistic band for the role’s level
        - **Keywords:** use the Keywords boolean; toggle 1–2 frameworks to tune
        """)
        fps = SMART_EXCLUDE_BASE + R.get("false_pos", []) + extra_not_list
        st.markdown("<div class='kicker' style='margin-top:.6rem'>Common NOT terms</div>", unsafe_allow_html=True)
        st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in fps]), unsafe_allow_html=True)

    # Outreach
    with tabs[5]:
        st.markdown("**Angles that resonate** (keep 1 short CTA)
", unsafe_allow_html=False)
        hooks = []
        cat_icons = {"swe":"🧱","frontend":"🎨","backend":"🧩","mobile_ios":"📱","mobile_android":"🤖","ml":"🧪","data_eng":"🗄️","data_analyst":"📊","pm":"🧭","design":"✏️","sre":"🚦","devops":"⚙️","security":"🛡️","solutions_arch":"🧰"}
        icon = cat_icons.get(cat, "✨")
        if cat in ["swe","backend","frontend","devops","sre"]:
            hooks = ["Own a core service at scale; modern stack (K8s/Cloud)", "Greenfield feature with autonomy & measurable impact"]
        elif cat == "ml":
            hooks = ["Ship models to prod fast (LLM/RecSys)", "GPU budget + modern tooling (Ray/MLflow)"]
        elif cat == "data_eng":
            hooks = ["Modern data stack (Spark/DBT/Snowflake)", "Own pipelines that unblock product teams"]
        elif cat == "data_analyst":
            hooks = ["Partner with PMs on experiment design", "Direct line from analysis → product decisions"]
        elif cat == "design":
            hooks = ["Product ownership + design system contributions", "Research‑to‑ship loop with real impact"]
        elif cat == "pm":
            hooks = ["High‑leverage platform surface area", "Clear metrics ownership (activation/retention)"]
        elif cat == "security":
            hooks = ["Own AppSec roadmap and threat modeling", "Budget/time for fixing systemic issues"]
        elif cat == "solutions_arch":
            hooks = ["Complex, technical pre‑sales with real engineering", "Autonomy over POCs and customer outcomes"]
        for h in hooks:
            st.markdown(f"- {icon} {h}")
        st.caption("No protected‑attribute targeting. Keep it candidate‑centric and skills‑based.")

    # Checklist
    with tabs[6]:
        st.markdown("""
        - ✅ Broad & Focused variants ready
        - ✅ NOT terms set (Smart + custom)
        - ✅ 1–2 frameworks toggled for volume control
        - ✅ Company filters selected (Top + Adjacent)
        - ✅ Outreach angle drafted with measurable impact
        - ✅ Save the best string for reuse on similar roles
        """)

    # Export
    with tabs[7]:
        pack = f"""
        ROLE: {any_title}
LOCATION: {location or 'N/A'}
CONFIDENCE: {score}/100

TITLES: {', '.join(titles)}
MUST: {', '.join(must)}
NICE: {', '.join(nice)}

LINKEDIN TITLE:
{li_title}

LINKEDIN KEYWORDS:
{li_keywords}

GOOGLE XRAY:
{google_xray}

VARIANT A (BROAD):
{broad_var}

VARIANT B (FOCUSED):
{focused_var}

NOT TERMS:
{', '.join(SMART_EXCLUDE_BASE + R.get('false_pos', []) + extra_not_list)}

COMPANIES (TOP):
{', '.join(R.get('top_companies', []))}

COMPANIES (ADJACENT):
{', '.join(R.get('adjacent', []))}

TEAM NAMES:
{', '.join(R.get('team_names', []))}
        """
        st.download_button("Download pack (.txt)", data=pack, file_name="sourcing_pack.txt")

else:
    st.info("Type **any job title**, optionally add a location and custom NOT terms, then click **Build sourcing pack**.")
