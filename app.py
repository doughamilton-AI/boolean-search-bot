# app_ai_wow.py — AI Sourcing Assistant (Bright UI + AI Builder stub + Sticky Copy + URL state)
# Copy this entire file into `app.py` (or set Streamlit main file path to `app_ai_wow.py`).
# Requires: streamlit>=1.31

import os, json, re
from typing import List, Tuple, Dict
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
    "customer support", "help desk", "desktop support", "qa tester", "graphic designer"
]

# ============================ Company Sets (top-tech + metros, editable) ============================
COMPANY_SETS = {
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

METRO_COMPANIES = {
    "Any": [],
    "Bay Area": ["Google", "Meta", "Apple", "Netflix", "NVIDIA", "Airbnb", "Stripe", "Uber", "Databricks", "Snowflake", "DoorDash"],
    "New York": ["Google", "Meta", "Amazon", "Spotify", "Datadog", "MongoDB", "Ramp", "Plaid", "Etsy"],
    "Seattle": ["Amazon", "Microsoft", "AWS", "Azure", "Tableau"],
    "Remote-first": ["GitLab", "Automattic", "Zapier", "Stripe", "Dropbox", "Doist"],
}

ROLE_TO_GROUPS = {
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
            seen.add(k); out.append(c)
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
    if any(t in s for t in ["sre", "site reliability", "reliab", "devops", "platform reliability"]):
        return "sre"
    if any(t in s for t in ["machine learning", "ml engineer", "applied scientist", "data scientist", "ai engineer", " ml ", "ml-", "ml/"]):
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
    base = unique_preserve(must + nice + (qualifiers or []))
    core = or_group(base)
    if not core:
        return ""
    nots2 = unique_preserve(nots)
    if not nots2:
        return core
    return core + " NOT (" + " OR ".join(nots2) + ")"


def jd_extract(jd_text: str) -> Tuple[List[str], List[str], List[str]]:
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
    depth = 0; ok = True
    for ch in s:
        if ch == "(": depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0: ok = False; break
    if depth != 0 or not ok:
        issues.append("Unbalanced parentheses; copy fresh strings or simplify.")
    return issues


def string_health_grade(s: str) -> str:
    if not s:
        return "F"
    score = 100
    if len(s) > 900: score -= 25
    orc = s.count(" OR ")
    if orc > 80: score -= 25
    if orc > 40: score -= 15
    if any(x in string_health_report(s) for x in ["Unbalanced parentheses"]):
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
            seen.add(xl); res.append(x)
    return res[:24]

# ============================ AI Builder (stub) ============================
SCHEMA_KEYS = ["titles", "skills", "not_terms", "company_or", "rationales"]

def call_llm(payload: Dict) -> Dict:
    """OpenAI-backed implementation using Structured Outputs (JSON Schema).
    Returns {} to trigger fallback if key/module unavailable or parsing fails.
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {}
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return {}

    client = OpenAI(api_key=key)

    # JSON Schema the model must follow (strict)
    schema: Dict = {
        "type": "object",
        "properties": {
            "role_family": {"type": "string", "enum": ["swe","ml","sre","data","security","mobile"]},
            "titles": {
                "type": "object",
                "properties": {
                    "must":   {"type": "array", "items": {"type": "string"}},
                    "variants":{"type": "array", "items": {"type": "string"}}
                },
                "required": ["must","variants"],
                "additionalProperties": False
            },
            "skills": {
                "type": "object",
                "properties": {
                    "must": {"type": "array", "items": {"type": "string"}},
                    "nice": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["must","nice"],
                "additionalProperties": False
            },
            "not_terms":  {"type": "array", "items": {"type": "string"}},
            "company_or": {"type": "array", "items": {"type": "string"}},
            "rationales": {
                "type": "object",
                "properties": {
                    "titles": {"type": "string"},
                    "skills": {"type": "string"},
                    "not_terms": {"type": "string"},
                    "company_or": {"type": "string"}
                },
                "additionalProperties": False
            }
        },
        "required": ["titles","skills","not_terms","company_or"],
        "additionalProperties": False
    }

    # Build prompts using ASCII-safe strings (double quotes) and a safe joiner
    sys_lines = [
        "You are an expert technical sourcer for top tech.",
        "Return JSON ONLY that matches the provided schema exactly.",
        "Prefer canonical skills and realistic titles from the ontology.",
        "Use synonyms map to normalize tokens (for example: golang->go, k8s->kubernetes).",
        "If uncertain, bias toward precision over coverage."
    ]
    joiner = chr(10)
    system_prompt = joiner.join(sys_lines)

    mode = payload.get("mode", "coverage")
    jt = payload.get("job_title", "") or ""
    jd = payload.get("job_description", "") or ""
    loc = payload.get("location", "") or ""

    context_obj = {
        "ontology": payload.get("ontology", {}),
        "synonyms": payload.get("synonyms", {}),
        "company_segments": payload.get("company_segments", {}),
        "caps": {"mode": mode, "titles": 22 if mode=="coverage" else 10}
    }
    user_lines = [
        "JOB_TITLE: " + jt,
        "LOCATION: " + loc,
        "MODE: " + mode,
        "JD:" + joiner + (jd if jd else "(none)"),
        "CONTEXT:" + joiner + json.dumps(context_obj, ensure_ascii=True)
    ]
    user_prompt = joiner.join(user_lines)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2 if mode == "precision" else 0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "SourcingPack",
                    "schema": schema,
                    "strict": True
                }
            },
        )
        content = completion.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return {}


def build_ai_pack(job_title: str, jd_text: str, location: str, mode: str) -> Dict | None:
    payload = {
        "job_title": job_title,
        "job_description": jd_text or "",
        "location": location or "",
        "mode": mode,
        "ontology": ROLE_LIB,
        "synonyms": SYNONYMS,
        "company_segments": COMPANY_SETS,
    }
    raw = call_llm(payload) or {}
    # If no usable keys, signal fallback
    if not any(k in raw for k in SCHEMA_KEYS):
        return None
    # Validate + canonicalize
    titles = canonicalize((raw.get("titles", {}).get("must", []) or []) + (raw.get("titles", {}).get("variants", []) or []))
    skills_must = canonicalize(raw.get("skills", {}).get("must", []) or [])
    skills_nice = canonicalize(raw.get("skills", {}).get("nice", []) or [])
    not_terms = canonicalize(raw.get("not_terms", []) or [])
    companies = canonicalize(raw.get("company_or", []) or [])
    # Cap by mode
    if mode == "precision":
        titles = titles[:10]; skills_must = skills_must[:12]; skills_nice = skills_nice[:6]; not_terms = not_terms[:8]; companies = companies[:20]
    else:
        titles = titles[:22]; skills_must = skills_must[:20]; skills_nice = skills_nice[:10]; not_terms = not_terms[:12]; companies = companies[:30]
    return {
        "titles": titles,
        "skills_must": skills_must,
        "skills_nice": skills_nice,
        "not_terms": not_terms,
        "companies": companies,
        "rationales": raw.get("rationales", {}),
    }

# ============================ Bright Theme CSS ============================
THEMES = {
    "Sky":   {"grad": "linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)", "bg": "#F8FAFC", "card": "#FFFFFF", "text": "#0F172A", "muted": "#475569", "ring": "#3B82F6", "button": "#2563EB"},
    "Coral": {"grad": "linear-gradient(135deg, #FB7185 0%, #F59E0B 100%)", "bg": "#FFF7ED", "card": "#FFFFFF", "text": "#111827", "muted": "#6B7280", "ring": "#F97316", "button": "#F97316"},
    "Mint":  {"grad": "linear-gradient(135deg, #34D399 0%, #22D3EE 100%)", "bg": "#ECFEFF", "card": "#FFFFFF", "text": "#0F172A", "muted": "#334155", "ring": "#10B981", "button": "#10B981"},
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
        ".sticky {position: fixed; left: 0; right: 0; bottom: 12px; z-index: 9999; display:flex; gap:8px; justify-content:center;}",
        ".sticky .btn {background: var(--btn); color:#fff; padding:8px 12px; border-radius:999px; font-weight:700; border:none;}",
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

# ============================ URL State ============================
qp = st.query_params

def qp_get(name: str, default: str = "") -> str:
    val = qp.get(name, None)
    # val can be a str or a list[str]
    if val is None:
        return default
    if isinstance(val, list):
        return val[0] if val else default
    return val or default


def qp_set(**kwargs):
    # Replace all params so the URL is stable/shareable
    qp.clear()
    for k, v in kwargs.items():
        # Streamlit accepts str or list[str]
        qp[k] = v

# ============================ UI: Inputs ============================
col_theme = st.columns([1])[0]
with col_theme:
    theme_choice = st.selectbox("Theme", list(THEMES.keys()), index=[*THEMES].index(qp_get("theme", "Sky")))
inject_css(theme_choice)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
left, right = st.columns([3, 2])
with left:
    job_title = st.text_input("Search by job title", value=qp_get("title", ""), placeholder="e.g., Staff Machine Learning Engineer")
with right:
    location = st.text_input("Location (optional)", value=qp_get("loc", ""), placeholder="e.g., New York, Remote, Bay Area")

extra_not = st.text_input("Extra NOT terms (comma-separated, optional)", value=qp_get("not", ""), placeholder="e.g., contractor, internship")

col1, col2, col3, col4 = st.columns(4)
with col1:
    level = st.selectbox("Seniority", ["All", "Associate", "Mid", "Senior+", "Staff/Principal"], index=["All","Associate","Mid","Senior+","Staff/Principal"].index(qp_get("level", "All")))
with col2:
    env = st.selectbox("Work setting", ["Any", "On-site", "Hybrid", "Remote"], index=["Any","On-site","Hybrid","Remote"].index(qp_get("env", "Any")))
with col3:
    size = st.selectbox("Company size", ["Any", "Startup", "Growth", "Enterprise"], index=["Any","Startup","Growth","Enterprise"].index(qp_get("size", "Any")))
with col4:
    metro = st.selectbox("Metro focus", list(METRO_COMPANIES.keys()), index=list(METRO_COMPANIES.keys()).index(qp_get("metro", "Any")))

ai_mode = st.toggle("🤖 Use AI Builder (beta)", value=(qp_get("aimode", "off") == "on"), help="Let AI propose titles/skills/NOT/companies. Falls back if unavailable.")

if st.button("✨ Build sourcing pack") and (job_title or "").strip():
    qp_set(title=job_title, loc=location, level=level, env=env, size=size, metro=metro, theme=theme_choice, aimode=("on" if ai_mode else "off"))
    st.session_state["built"] = True
    st.session_state["role_title"] = job_title
    st.session_state["location"] = location
    st.session_state["category"] = map_title_to_category(job_title)

    # Default packs from ontology
    R = ROLE_LIB[st.session_state["category"]]
    titles_seed = expand_titles(R["titles"], st.session_state["category"])    
    must_seed = list(R["must"]) 
    nice_seed = list(R["nice"]) 
    not_seed = list(SMART_NOT)
    companies_seed = []

    # Optionally AI augment
    if ai_mode:
        ai = build_ai_pack(job_title, "", location, mode=("precision" if level in ["Senior+","Staff/Principal"] else "coverage"))
        if ai:
            titles_seed = unique_preserve(ai.get("titles", []) + titles_seed)
            must_seed = unique_preserve(ai.get("skills_must", []) + must_seed)
            nice_seed = unique_preserve(ai.get("skills_nice", []) + nice_seed)
            not_seed = unique_preserve(not_seed + ai.get("not_terms", []))
            companies_seed = unique_preserve(ai.get("companies", []))
        else:
            st.info("AI Builder unavailable; using heuristic pack.")

    st.session_state["titles"] = titles_seed
    st.session_state["must"] = must_seed
    st.session_state["nice"] = nice_seed
    st.session_state["not_terms"] = not_seed
    st.session_state["companies_ai"] = companies_seed

category = st.session_state.get("category", "")
hero(st.session_state.get("role_title", ""), category, st.session_state.get("location", ""))

if st.session_state.get("built"):
    titles = st.session_state.get("titles", [])
    must = st.session_state.get("must", [])
    nice = st.session_state.get("nice", [])
    base_not = st.session_state.get("not_terms", [])

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Auto-infer seniority from title text (light heuristic)
    title_lower = (st.session_state.get("role_title", "") or "").lower()
    if any(w in title_lower for w in ["staff", "principal"]):
        level = "Staff/Principal"
    elif any(w in title_lower for w in ["senior", "sr "]):
        level = "Senior+"

    # Seniority adjustment affects title set for LinkedIn title fields
    titles = apply_seniority(titles, level)

    # Editors (always visible)
    st.subheader("✏️ Customize")
    c1, c2 = st.columns([1, 1])
    with c1:
        newline = chr(10)
        titles_default = newline.join(titles)
        titles_text = st.text_area("Titles (one per line)", value=titles_default, height=160)
    with c2:
        comma_space = chr(44) + chr(32)
        must_default = comma_space.join(must)
        must_text = st.text_area("Must-have skills (comma-separated)", value=must_default, height=120)
        nice_default = comma_space.join(nice)
        nice_text = st.text_area("Nice-to-have skills (comma-separated)", value=nice_default, height=120)

    # JD extraction (optional)
    with st.expander("📄 Paste JD → Auto-extract (optional)"):
        jd = st.text_area("Paste JD (optional)", height=160)
        if st.button("Extract from JD"):
            m_ex, n_ex, n_not = jd_extract(jd)
            applied = False
            if m_ex:
                must = unique_preserve(m_ex + must); applied = True
            if n_ex:
                nice = unique_preserve(n_ex + nice); applied = True
            if n_not:
                base_not = unique_preserve(base_not + n_not); applied = True
            if applied:
                st.success("JD terms applied.")
            else:
                st.info("No strong matches found.")

    # Apply user edits
    if st.button("Apply changes"):
        titles = [t.strip() for t in titles_text.splitlines() if t.strip()]
        must = [s.strip() for s in must_text.split(",") if s.strip()]
        nice = [s.strip() for s in nice_text.split(",") if s.strip()]
        st.session_state["titles"], st.session_state["must"], st.session_state["nice"] = titles, must, nice

    # Company targets (segments + metro + custom add)
    st.subheader("🏢 Company Targets — common employers for this role")
    group_order = ROLE_TO_GROUPS.get(category or "swe", ["faang_plus"]) 
    default_sel = group_order[:3] if len(group_order) >= 3 else group_order
    selected_groups = st.multiselect("Segments", options=group_order, default=default_sel, help="Choose segments to populate the company list.")
    custom_companies = st.text_area("Add companies (comma-separated)", placeholder="e.g., Two Sigma, Bloomberg, Robinhood", height=80)

    companies = []
    for g in selected_groups:
        companies.extend(COMPANY_SETS.get(g, []))
    companies.extend(METRO_COMPANIES.get(metro, []))
    companies.extend(st.session_state.get("companies_ai", []))
    companies.extend([c.strip() for c in (custom_companies or "").split(",") if c.strip()])
    companies = unique_preserve(companies)

    # Qualifiers bias Keywords only
    qual = []
    if env == "Remote": qual.append("remote")
    elif env == "Hybrid": qual.append("hybrid")
    elif env == "On-site": qual.append("on-site")
    if size == "Startup": qual.append("startup")
    elif size == "Growth": qual.append("scale-up")
    elif size == "Enterprise": qual.append("enterprise")
    qual = qual + ["highly scalable", "high throughput"]

    # Build strings
    extra_not_list = [t.strip() for t in (extra_not or "").split(",") if t.strip()]
    all_not = unique_preserve(base_not + extra_not_list)
    li_title_current = or_group(titles)
    li_title_past = or_group(titles[: min(20, len(titles))])
    li_keywords = build_keywords(canonicalize(must), canonicalize(nice), canonicalize(all_not), qualifiers=canonicalize(qual))
    companies_or = or_group(companies)
    skills_all_csv = ", ".join(unique_preserve(must + nice))

    # Health + grade + quick fix
    issues = string_health_report(li_keywords)
    grade = string_health_grade(li_keywords)
    if issues:
        joiner = chr(10)
        st.warning("Health: " + grade + joiner + joiner.join(["• " + x for x in issues]))
        if st.button("🧹 Trim & Dedupe (suggested)"):
            # Simple trim: keep top-k of must/nice; rebuild
            must_k = canonicalize(must)[:12]
            nice_k = canonicalize(nice)[:8]
            all_not_k = canonicalize(all_not)[:10]
            li_keywords = build_keywords(must_k, nice_k, all_not_k, qualifiers=canonicalize(qual))
            st.success("Applied trim/dedupe.")
    else:
        st.success("✅ String looks healthy (" + grade + ") and ready to paste into LinkedIn.")
        st.balloons()

    # Blocks
    st.subheader("🎯 Boolean Pack (LinkedIn fields)")
    st.caption("Each block is copyable — paste into the matching LinkedIn field.")
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    code_card("Title (Current) • People → Title (Current)", li_title_current)
    code_card("Title (Past) • People → Title (Past)", li_title_past)
    code_card("Keywords (Boolean) • People → Keywords", li_keywords)
    code_card("Companies (OR) • People → Current/Past company", companies_or)
    st.markdown("</div>", unsafe_allow_html=True)

    # Export
    st.subheader("⬇️ Export")
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
    joiner = chr(10)
    pack_text = joiner.join(lines)
    st.download_button("Download pack (.txt)", data=pack_text, file_name="sourcing_pack.txt")

    # Sticky Copy Bar (copy 4 key blocks)
    def js_escape(s: str) -> str:
        try:
            return json.dumps(s or "")
        except Exception:
            return json.dumps("")
    html = []
    html.append("<div class='sticky'>")
    html.append("<button class='btn' onclick=\"navigator.clipboard.writeText(" + js_escape(li_title_current) + ")\">Copy Title(Current)</button>")
    html.append("<button class='btn' onclick=\"navigator.clipboard.writeText(" + js_escape(li_title_past) + ")\">Copy Title(Past)</button>")
    html.append("<button class='btn' onclick=\"navigator.clipboard.writeText(" + js_escape(li_keywords) + ")\">Copy Keywords</button>")
    html.append("<button class='btn' onclick=\"navigator.clipboard.writeText(" + js_escape(companies_or) + ")\">Copy Companies</button>")
    html.append("</div>")
    st.components.v1.html("".join(html), height=70)

    # Guidance
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.subheader("💡 Pro tips for LinkedIn Recruiter")
    st.markdown("- Put **Title (Current)** and **Title (Past)** into their matching fields.")
    st.markdown("- Use **Keywords** for skills, frameworks, and context (we add work setting/size qualifiers here).")
    st.markdown("- Use **Companies (OR)** in **Current/Past company** to target alumni.")
    st.markdown("- Apply location filters in LinkedIn separately—keeps strings portable.")
    st.markdown("- If volume is too high, use Seniority = Senior+/Staff and click **Trim & Dedupe**.")

else:
    st.info("Type a job title (try 'Staff Machine Learning Engineer'), pick a bright theme, then click **Build sourcing pack**.")
