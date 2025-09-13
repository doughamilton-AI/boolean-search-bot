# app.py — AI Sourcing Assistant (Bright UI, No External AI)
# Requirements (requirements.txt):
# streamlit>=1.33

import json
import re
from typing import List, Tuple, Dict
import streamlit as st

st.set_page_config(page_title="AI Sourcing Assistant", layout="wide")

# ============================ Role Library (extensible) ============================
ROLE_LIB: Dict[str, Dict[str, List[str]]] = {
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
    "customer support", "help desk", "desktop support", "qa tester", "graphic designer"
]

# ============================ Company Sets (top-tech + metros, editable) ============================
COMPANY_SETS: Dict[str, List[str]] = {
    "faang_plus": [
        "Google", "Meta", "Apple", "Amazon", "Netflix", "Microsoft",
        "NVIDIA", "Uber", "Airbnb", "Stripe", "Dropbox", "LinkedIn"
    ],
    "cloud_infra": [
        "AWS", "Azure", "Google Cloud", "Cloudflare", "Snowflake", "Datadog",
        "Fastly", "Akamai", "HashiCorp", "DigitalOcean", "Twilio", "MongoDB"
    ],
    "ai_first": [
        "OpenAI", "Anthropic", "DeepMind", "Hugging Face", "Stability AI",
        "Cohere", "Scale AI", "Character AI", "Perplexity AI", "xAI"
    ],
    "devtools_data": [
        "Databricks", "Confluent", "Elastic", "Snyk", "GitHub", "GitLab",
        "JetBrains", "CircleCI", "PagerDuty", "New Relic", "Grafana Labs", "Postman"
    ],
    "enterprise_saas": [
        "Salesforce", "ServiceNow", "Workday", "Atlassian", "Slack",
        "Notion", "Asana", "Zoom", "Box", "Dropbox"
    ],
    "consumer_social": [
        "YouTube", "Instagram", "WhatsApp", "Snap", "TikTok", "Pinterest",
        "Reddit", "Spotify", "Discord"
    ],
    "fintech": [
        "Stripe", "Square", "Plaid", "Coinbase", "Robinhood", "Brex",
        "Ramp", "Affirm", "Chime", "SoFi"
    ],
    "marketplaces": [
        "Uber", "Lyft", "DoorDash", "Instacart", "Airbnb", "Etsy",
        "Amazon Marketplace", "Shopify"
    ],
    "high_growth": [
        "Rippling", "Figma", "Canva", "Retool", "Glean", "Snowflake",
        "Databricks", "Cloudflare", "Notion", "Scale AI"
    ],
}

METRO_COMPANIES: Dict[str, List[str]] = {
    "Any": [],
    "Bay Area": ["Google", "Meta", "Apple", "Netflix", "NVIDIA", "Airbnb", "Stripe", "Uber", "Databricks", "Snowflake", "DoorDash"],
    "New York": ["Google", "Meta", "Amazon", "Spotify", "Datadog", "MongoDB", "Ramp", "Plaid", "Etsy"],
    "Seattle": ["Amazon", "Microsoft", "AWS", "Azure", "Tableau"],
    "Remote-first": ["GitLab", "Automattic", "Zapier", "Stripe", "Dropbox", "Doist"],
}

ROLE_TO_GROUPS: Dict[str, List[str]] = {
    "swe": ["faang_plus", "devtools_data", "enterprise_saas", "cloud_infra", "consumer_social", "fintech", "marketplaces", "high_growth"],
    "ml":  ["ai_first", "faang_plus", "cloud_infra", "devtools_data", "enterprise_saas", "consumer_social", "high_growth"],
    "sre": ["cloud_infra", "faang_plus", "devtools_data", "enterprise_saas", "marketplaces", "high_growth"],
}

# ============================ Synonyms (canonicalization) ============================
SYNONYMS: Dict[str, str] = {
    "golang": "go",
    "k8s": "kubernetes",
    "llm": "large language model",
    "tf": "tensorflow",
    "py": "python",
}

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


def canonicalize(tokens: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tokens:
        c = SYNONYMS.get((t or "").lower(), t or "").strip()
        k = c.lower()
        if k and k not in seen:
            seen.add(k)
            out.append(c)
    return out


def normalize_quotes(s: str) -> str:
    return (s or "").replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")


def safe_quote(token: str) -> str:
    t = normalize_quotes((token or "").strip())
    if not t:
        return ""
    t = t.replace('"', r'\"')  # escape embedded quotes
    # quote if contains whitespace or parens/ops/hyphenated terms
    if re.search(r"\s|\(|\)|-", t):
        return f'"{t}"'
    return t


def or_group(items: List[str]) -> str:
    toks = [safe_quote(i) for i in items if i and i.strip()]
    toks = unique_preserve([t for t in toks if t])
    return f"({ ' OR '.join(toks) })" if toks else ""


def not_group(items: List[str]) -> str:
    toks = [safe_quote(i) for i in items if i and i.strip()]
    toks = unique_preserve([t for t in toks if t])
    return f"({ ' OR '.join(toks) })" if toks else ""


def map_title_to_category(title: str) -> str:
    s = (title or "").lower()
    if any(t in s for t in ["sre", "site reliability", "reliab", "devops", "platform reliability", "production engineer"]):
        return "sre"
    if any(t in s for t in [
        "machine learning", "ml engineer", "applied scientist", "data scientist", "ai engineer",
        "genai", "llm", "deep learning", " ml ", "ml-", "ml/"
    ]):
        return "ml"
    return "swe"


def expand_titles(base_titles: List[str], cat: str) -> List[str]:
    extra: List[str] = []
    if cat == "swe":
        extra = ["Software Eng", "Software Dev", "Full-Stack Engineer", "Backend Developer", "Frontend Developer"]
    elif cat == "ml":
        extra = ["ML Eng", "Machine Learning Specialist", "Applied ML Engineer", "ML Research Engineer"]
    elif cat == "sre":
        extra = ["Reliability Eng", "DevOps SRE", "Platform SRE", "Production Engineer"]
    return unique_preserve(base_titles + extra)


def build_keywords(must: List[str], nice: List[str], nots: List[str], qualifiers: List[str] = None) -> str:
    core = or_group(unique_preserve(canonicalize(must) + canonicalize(nice) + canonicalize(qualifiers or [])))
    if not core:
        return ""
    ng = not_group(unique_preserve(canonicalize(nots)))
    return f"{core} NOT {ng}" if ng else core


def build_keywords_two_tier(must: List[str], nice: List[str], nots: List[str], qualifiers: List[str] = None, min_must: int = 2) -> str:
    must = canonicalize(must)
    anchors, rest = must[:max(0, min_must)], must[max(0, min_must):]
    left = " AND ".join(or_group([a]) for a in anchors) if anchors else ""
    right = or_group(unique_preserve(rest + canonicalize(nice) + canonicalize(qualifiers or [])))
    core = " AND ".join([p for p in [left, right] if p])
    ng = not_group(unique_preserve(canonicalize(nots)))
    return f"{core} NOT {ng}" if ng else core


def jd_extract(jd_text: str) -> Tuple[List[str], List[str], List[str]]:
    jd = normalize_quotes((jd_text or "").lower())
    pool = {s.lower() for role in ROLE_LIB.values() for s in (role["must"] + role["nice"])}

    def count_term(term: str) -> int:
        if " " in term or "/" in term or "-" in term:
            return jd.count(term)
        return len(re.findall(rf"\b{re.escape(term)}\b", jd))

    ranked = [t for t in sorted(pool, key=lambda x: count_term(x), reverse=True) if count_term(t) > 0]
    must_ex, nice_ex = ranked[:8], ranked[8:16]
    auto_not_terms = ["intern", "contract", "temporary", "help desk", "desktop support", "qa tester", "graphic designer"]
    auto_not = [kw for kw in auto_not_terms if re.search(rf"\b{re.escape(kw)}\b", jd)]
    return must_ex, nice_ex, auto_not


def string_health_report(s: str) -> List[str]:
    issues: List[str] = []
    if not s:
        return ["Keywords are empty — add must/nice skills."]
    if len(s) > 900:
        issues.append("Keywords look long (>900 chars); consider trimming.")
    if s.count(" OR ") > 80:
        issues.append("High OR count; remove niche/redundant terms.")
    # Ignore quoted segments when checking parentheses balance
    unquoted = re.sub(r'"[^"]*"', "", s)
    depth = 0
    ok = True
    for ch in unquoted:
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


def string_health_grade(s: str) -> str:
    if not s:
        return "F"
    score = 100
    if len(s) > 900:
        score -= 25
    orc = s.count(" OR ")
    if orc > 80:
        score -= 25
    if orc > 40:
        score -= 15
    if any("Unbalanced parentheses" in x for x in string_health_report(s)):
        score -= 25
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "E" if score >= 50 else "F"


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
    else:
        out = ["Staff " + b for b in base] + ["Principal " + b for b in base] + ["Lead " + b for b in base] + base
    seen, res = set(), []
    for x in out:
        xl = x.lower()
        if xl not in seen:
            seen.add(xl)
            res.append(x)
    return res[:24]

# ============================ Bright Theme CSS ============================
THEMES: Dict[str, Dict[str, str]] = {
    "Sky":   {"grad": "linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)", "bg": "#F8FAFC", "card": "#FFFFFF", "text": "#0F172A", "muted": "#475569", "ring": "#3B82F6", "button": "#2563EB"},
    "Coral": {"grad": "linear-gradient(135deg, #FB7185 0%, #F59E0B 100%)", "bg": "#FFF7ED", "card": "#FFFFFF", "text": "#111827", "muted": "#6B7280", "ring": "#F97316", "button": "#F97316"},
    "Mint":  {"grad": "linear-gradient(135deg, #34D399 0%, #22D3EE 100%)", "bg": "#ECFEFF", "card": "#FFFFFF", "text": "#0F172A", "muted": "#334155", "ring": "#10B981", "button": "#10B981"},
}


def inject_css(theme_name: str) -> None:
    t = THEMES.get(theme_name, THEMES["Sky"])
    css = f"""
    <style>
      :root {{
        --grad: {t['grad']};
        --bg: {t['bg']};
        --card: {t['card']};
        --text: {t['text']};
        --muted: {t['muted']};
        --ring: {t['ring']};
        --btn: {t['button']};
        --gap: 16px;
        --pad: 14px;
        --radius: 16px;
        --codefs: 12.5px;
        --btnpad: 9px 14px;
      }}
      .stApp, [data-testid='stAppViewContainer'] {{ background: var(--bg); color: var(--text); }}
      [data-testid='stHeader'] {{ background: transparent; }}
      .hero {{
        padding: var(--pad);
        border-radius: var(--radius);
        background: var(--card);
        border: 1px solid rgba(0,0,0,.06);
        box-shadow: 0 6px 24px rgba(2,6,23,.06);
        margin-bottom: var(--gap);
      }}
      .hero h1 {{
        margin: 0;
        font-size: 28px;
        font-weight: 800;
        background: var(--grad);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
      }}
      .chips {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }}
      .chip {{
        padding: 6px 10px; border-radius: 999px; font-size: 12px; color: var(--text);
        background: rgba(2,6,23,.04); border: 1px solid rgba(2,6,23,.06);
      }}
      input[type='text'], textarea {{
        background: var(--card) !important; color: var(--text) !important;
        border: 1px solid rgba(2,6,23,.08) !important; border-radius: var(--radius) !important;
      }}
      input[type='text']:focus, textarea:focus {{
        outline: none !important; border-color: var(--ring) !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,.18) !important;
      }}
      .stButton>button, .stDownloadButton>button {{
        background: var(--btn); color: #FFFFFF; font-weight: 700; border: none;
        padding: var(--btnpad); border-radius: 999px; box-shadow: 0 10px 24px rgba(2,6,23,.12);
      }}
      .stButton>button:hover, .stDownloadButton>button:hover {{ filter: brightness(1.05); }}
      .stButton>button:focus {{ outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.25); }}
      pre, code {{ font-size: var(--codefs) !important; }}
      .grid {{ display: grid; gap: var(--gap); grid-template-columns: repeat(12, 1fr); }}
      .card {{
        grid-column: span 6; background: var(--card); border: 1px solid rgba(2,6,23,.06);
        border-radius: var(--radius); padding: var(--pad); box-shadow: 0 6px 24px rgba(2,6,23,.06);
      }}
      .hint {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
      .divider {{ height: 1px; background: linear-gradient(90deg, transparent, rgba(2,6,23,.15), transparent); margin: 8px 0; }}
      .sticky {{
        position: fixed; left: 0; right: 0; bottom: 12px; z-index: 9999; display:flex;
        gap:8px; justify-content:center;
      }}
      .sticky .btn {{
        background: var(--btn); color:#fff; padding:8px 12px; border-radius:999px; font-weight:700; border:none;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


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

# ============================ URL State ============================
qp = st.query_params


def qp_get(name: str, default: str = "") -> str:
    val = qp.get(name, None)
    if val is None:
        return default
    if isinstance(val, list):
        return val[0] if val else default
    return val or default


def qp_set(**kwargs):
    for k, v in kwargs.items():
        st.query_params[k] = v

# ============================ UI: Inputs ============================
col_theme = st.columns([1])[0]
with col_theme:
    default_theme = qp_get("theme", "Sky")
    if default_theme not in THEMES:
        default_theme = "Sky"
    theme_choice = st.selectbox("Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(default_theme))
inject_css(theme_choice)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
left, right = st.columns([3, 2])
with left:
    job_title = st.text_input("Search by job title", value=qp_get("title", ""), placeholder="e.g., Staff Machine Learning Engineer")
with right:
    location = st.text_input("Location (optional)", value=qp_get("loc", ""), placeholder="e.g., New York, Remote, Bay Area")

extra_not = st.text_input("Extra NOT terms (comma-separated, optional)", value=qp_get("not", ""), placeholder="e.g., contractor, internship", key="extra_not")

col1, col2, col3, col4 = st.columns(4)
with col1:
    level = st.selectbox("Seniority", ["All", "Associate", "Mid", "Senior+", "Staff/Principal"], index=["All","Associate","Mid","Senior+","Staff/Principal"].index(qp_get("level", "All")))
with col2:
    env = st.selectbox("Work setting", ["Any", "On-site", "Hybrid", "Remote"], index=["Any","On-site","Hybrid","Remote"].index(qp_get("env", "Any")))
with col3:
    size = st.selectbox("Company size", ["Any", "Startup", "Growth", "Enterprise"], index=["Any","Startup","Growth","Enterprise"].index(qp_get("size", "Any")))
with col4:
    metro_default = qp_get("metro", "Any")
    if metro_default not in METRO_COMPANIES:
        metro_default = "Any"
    metro = st.selectbox("Metro focus", list(METRO_COMPANIES.keys()), index=list(METRO_COMPANIES.keys()).index(metro_default))

# Build
if st.button("✨ Build sourcing pack") and (job_title or "").strip():
    qp_set(**{"title": job_title, "loc": location, "level": level, "env": env, "size": size, "metro": metro, "theme": theme_choice, "not": st.session_state.get("extra_not", "")})
    st.session_state["built"] = True
    st.session_state["role_title"] = job_title
    st.session_state["location"] = location
    st.session_state["category"] = map_title_to_category(job_title)

    R = ROLE_LIB[st.session_state["category"]]
    titles_seed = expand_titles(R["titles"], st.session_state["category"])
    must_seed = list(R["must"])
    nice_seed = list(R["nice"])
    not_seed = list(SMART_NOT)

    st.session_state["titles"] = titles_seed
    st.session_state["must"] = must_seed
    st.session_state["nice"] = nice_seed
    st.session_state["not_terms"] = not_seed

category = st.session_state.get("category", "")
hero(st.session_state.get("role_title", ""), category, st.session_state.get("location", ""))

if st.session_state.get("built"):
    titles = st.session_state.get("titles", [])
    must = st.session_state.get("must", [])
    nice = st.session_state.get("nice", [])
    base_not = st.session_state.get("not_terms", [])

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Heuristic seniority from title
    title_lower = (st.session_state.get("role_title", "") or "").lower()
    if any(w in title_lower for w in ["staff", "principal"]):
        level = "Staff/Principal"
    elif any(w in title_lower for w in ["senior", "sr "]):
        level = "Senior+"

    titles = apply_seniority(titles, level)

    # Editors + advanced controls
    st.subheader("✏️ Customize")
    c0, c1, c2 = st.columns([1, 1, 1])
    with c0:
        ic_only = st.checkbox("IC-only (exclude managers)", value=False, help="Adds NOT manager/director/head of")
        use_two_tier = st.checkbox("Use must-have anchors (AND)", value=False, help="Require 1–2 anchors; everything else stays OR")
        min_must = st.slider("Anchors count", min_value=1, max_value=3, value=2, disabled=not use_two_tier)
        env_size_as_keywords = st.checkbox("Also add env/size as keywords", value=False, help="When filters aren't available; may increase noise")
    with c1:
        titles_text = st.text_area("Titles (one per line)", value="\n".join(titles), height=180, key="titles_text")
    with c2:
        must_text = st.text_area("Must-have skills (comma-separated)", value=", ".join(must), height=120, key="must_text")
        nice_text = st.text_area("Nice-to-have skills (comma-separated)", value=", ".join(nice), height=120, key="nice_text")

    # JD extraction (optional)
    with st.expander("📄 Paste JD → Auto-extract (optional)"):
        jd = st.text_area("Paste JD (optional)", height=160, key="jd_text")
        if st.button("Extract from JD"):
            m_ex, n_ex, n_not = jd_extract(jd)
            applied = False
            if m_ex:
                st.session_state["must"] = unique_preserve(st.session_state.get("must", []) + m_ex); applied = True
            if n_ex:
                st.session_state["nice"] = unique_preserve(st.session_state.get("nice", []) + n_ex); applied = True
            if n_not:
                st.session_state["not_terms"] = unique_preserve(st.session_state.get("not_terms", []) + n_not); applied = True
            if applied:
                st.session_state["must_text"] = ", ".join(st.session_state["must"])  # reflect in editor
                st.session_state["nice_text"] = ", ".join(st.session_state["nice"])
                st.success("JD terms applied to the editors.")
            else:
                st.info("No strong matches found.")

    # Apply user edits
    if st.button("Apply changes"):
        titles = [t.strip() for t in st.session_state.get("titles_text", "").splitlines() if t.strip()]
        must = [s.strip() for s in st.session_state.get("must_text", "").split(",") if s.strip()]
        nice = [s.strip() for s in st.session_state.get("nice_text", "").split(",") if s.strip()]
        st.session_state["titles"], st.session_state["must"], st.session_state["nice"] = titles, must, nice

    # Companies
    st.subheader("🏢 Company Targets — common employers for this role")
    group_order = ROLE_TO_GROUPS.get(category or "swe", ["faang_plus"])
    default_sel = group_order[:3] if len(group_order) >= 3 else group_order
    selected_groups = st.multiselect("Segments", options=group_order, default=default_sel, help="Choose segments to populate the company list.")
    custom_companies = st.text_area("Add companies (comma-separated)", placeholder="e.g., Two Sigma, Bloomberg, Robinhood", height=80)

    companies = []
    for g in selected_groups:
        companies.extend(COMPANY_SETS.get(g, []))
    companies.extend(METRO_COMPANIES.get(metro, []))
    companies.extend([c.strip() for c in (custom_companies or "").split(",") if c.strip()])
    companies = unique_preserve(companies)

    # Qualifiers (in Keywords)
    qual = []
    if env_size_as_keywords:
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
        # performance modifiers (optional flavor)
        qual += ["highly scalable", "high throughput"]

    # Build NOT list (IC-only optional)
    extra_not_list = [t.strip() for t in (st.session_state.get("extra_not", "") or "").split(",") if t.strip()]
    all_not = unique_preserve(base_not + extra_not_list)
    if ic_only:
        all_not = unique_preserve(all_not + ["manager", "director", "head of"])

    # Build strings
    li_title_current = or_group(titles)
    li_title_past = or_group(titles[: min(20, len(titles))])
    if use_two_tier:
        li_keywords = build_keywords_two_tier(must, nice, all_not, qualifiers=qual, min_must=min_must)
    else:
        li_keywords = build_keywords(must, nice, all_not, qualifiers=qual)
    companies_or = or_group(companies)
    skills_all_csv = ", ".join(unique_preserve(must + nice))

    # Health + grade + quick fix
    issues = string_health_report(li_keywords)
    grade = string_health_grade(li_keywords)
    if issues:
        st.warning("Health: " + grade + "\n" + "\n".join(["• " + x for x in issues]))
        if st.button("🧹 Trim & Dedupe (suggested)"):
            must_k = canonicalize(must)[:12]
            nice_k = canonicalize(nice)[:8]
            all_not_k = canonicalize(all_not)[:10]
            if use_two_tier:
                li_keywords = build_keywords_two_tier(must_k, nice_k, all_not_k, qualifiers=canonicalize(qual), min_must=min_must)
            else:
                li_keywords = build_keywords(must_k, nice_k, all_not_k, qualifiers=canonicalize(qual))
            st.success("Applied trim/dedupe.")
    else:
        st.success("✅ String looks healthy (" + grade + ") and ready to paste into LinkedIn.")
        st.balloons()

    # Boolean Pack
    st.subheader("🎯 Boolean Pack (LinkedIn fields)")
    st.caption("Each block is copyable — paste into the matching LinkedIn field.")
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    code_card("Title (Current) • People → Title (Current)", li_title_current)
    code_card("Title (Past) • People → Title (Past)", li_title_past)
    code_card("Keywords (Boolean) • People → Keywords", li_keywords)
    code_card("Companies (OR) • People → Current/Past company", companies_or)
    st.markdown("</div>", unsafe_allow_html=True)

    # Build export text (used below and in Export tab)
    lines: List[str] = []
    lines.append("ROLE: " + st.session_state.get("role_title", ""))
    lines.append("LOCATION: " + (st.session_state.get("location") or ""))
    lines.append("")
    lines.append("COMPANIES (OR):")
    lines.append(companies_or)
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

    # Assistant Panels
    st.subheader("📚 Assistant Panels")
    tabs = st.tabs(["🧠 Role Intel", "🌐 Signals", "🏢 Company Maps", "🚦 Filters", "💌 Outreach", "✅ Checklist", "⬇️ Export"])

    with tabs[0]:
        st.markdown("**What this shows:** quick context for the role, common responsibilities, and what *not* to target.")
        if category == "ml":
            st.markdown(
                """
- **Focus:** production ML (training → deployment), feature pipelines, model monitoring.
- **Common stacks:** Python, PyTorch/TensorFlow, Airflow, MLflow/Feature Store, AWS/GCP.
- **Avoid:** pure research-only profiles when you need prod ML; BI/marketing analysts.
                """
            )
        elif category == "sre":
            st.markdown(
                """
- **Focus:** reliability, incident response, infra as code, observability.
- **Common stacks:** Kubernetes, Terraform, Prometheus/Grafana, Go/Python, AWS/GCP.
- **Avoid:** Help Desk/IT support, QA-only.
                """
            )
        else:
            st.markdown(
                """
- **Focus:** building services and features, code quality, scalability.
- **Common stacks:** Python/Java/Go, microservices, Docker/Kubernetes, AWS/GCP.
- **Avoid:** QA-only, desktop support.
                """
            )
        st.markdown("**Title synonyms:**")
        st.code("\n".join(titles), language="text")
        st.markdown("**Top skills:**")
        st.code(", ".join(unique_preserve(must + nice)) or "python, java, go", language="text")

    with tabs[1]:
        st.markdown("**What this shows:** quick levers to tighten or widen results based on signal strength.")
        st.markdown(
            """
- Use **Title (Current)** first; if low volume, add **Title (Past)**.
- Start with **Keywords** then add/remove 2–3 skills to control volume.
- Add **NOT** terms like `intern, help desk, QA` to reduce noise.
            """
        )
        st.markdown("**Your current NOT terms:**")
        st.code(", ".join(all_not) or "intern, internship, help desk", language="text")

    with tabs[2]:
        st.markdown("**What this shows:** companies that commonly employ this role. Paste into Company filters or use as a target list.")
        st.code(companies_or or "(\"Google\" OR \"Meta\")", language="text")
        st.markdown("**List view:**")
        st.write(companies or ["Google", "Meta", "Amazon"])

    with tabs[3]:
        st.markdown("**What this shows:** suggested LinkedIn filters for this search.")
        filt = []
        if level == "Senior+":
            filt.append("Seniority: Senior")
        if level == "Staff/Principal":
            filt.append("Seniority: Staff/Principal (or 8–12+ years)")
        if env != "Any":
            filt.append(f"Work setting: {env}")
        if size != "Any":
            filt.append(f"Company size: {size}")
        if location:
            filt.append(f"Location: {location}")
        if ic_only:
            filt.append("Exclude managers: ON (NOT manager/director/head of)")
        st.write(filt or ["Seniority: Any", "Company size: Any"])
        st.markdown("**Tip:** If volume is high, add `current company = any` and rely on Titles + Keywords.")

    with tabs[4]:
        st.markdown("**What this shows:** 2 short, friendly outreach drafts you can personalize and send fast.")
        outreach_a = (
            f"""Subject: {st.session_state.get('role_title','')} impact at our team

Hi {{name}},
I’m hiring for a {st.session_state.get('role_title','')} to build {{impact area}}. Your background with {{relevant tech}} stood out. Interested in a quick chat?
— {{recruiter}}"""
        )
        outreach_b = (
            f"""Subject: {st.session_state.get('role_title','')} — fast chat?

Hi {{name}},
We’re scaling {{team/product}}. Your experience across {', '.join(must[:5]) or 'backend, infra'} looks like a great fit. 15 mins to explore?
— {{recruiter}}"""
        )
        st.code(outreach_a, language="text")
        st.code(outreach_b, language="text")

    with tabs[5]:
        st.markdown("**What this shows:** a quick start checklist to de-risk your search.")
        st.markdown(
            """
- Confirm role scope & must-haves with hiring manager.
- Align on 3–5 anchor companies to target first.
- Decide precision vs coverage strategy.
- Save the search; schedule a daily review.
            """
        )

    with tabs[6]:
        st.markdown("**What this shows:** the same export pack as below, for convenience.")
        st.code(pack_text, language="text")

    # Export (download)
    st.subheader("⬇️ Export")
    st.download_button("Download pack (.txt)", data=pack_text, file_name="sourcing_pack.txt")

    # Sticky Copy Bar (with fallback if navigator.clipboard is unavailable)
    def js_escape(s: str) -> str:
        try:
            return json.dumps(s or "")
        except Exception:
            return json.dumps("")

    html = []
    html.append("<div class='sticky'>")
    html.append("""
    <script>
      function fallbackCopy(text){
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch(e) {}
        document.body.removeChild(ta);
      }
      async function copyText(t){
        try{ if(navigator.clipboard){ await navigator.clipboard.writeText(t); }
              else { fallbackCopy(t); } }
        catch(e){ fallbackCopy(t); }
      }
    </script>
    """)
    html.append("<button class='btn' onclick=\"copyText(" + js_escape(li_title_current) + ")\">Copy Title(Current)</button>")
    html.append("<button class='btn' onclick=\"copyText(" + js_escape(li_title_past) + ")\">Copy Title(Past)</button>")
    html.append("<button class='btn' onclick=\"copyText(" + js_escape(li_keywords) + ")\">Copy Keywords</button>")
    html.append("<button class='btn' onclick=\"copyText(" + js_escape(companies_or) + ")\">Copy Companies</button>")
    html.append("</div>")
    st.components.v1.html("".join(html), height=90)

# Final hint if user hasn't built yet
if not st.session_state.get("built"):
    st.info("Type a job title (try 'Staff Machine Learning Engineer'), pick a bright theme, then click **Build sourcing pack**.")
