# app.py — AI Sourcing Assistant (Bright UI, No External AI)
# Requirements (requirements.txt):
# streamlit>=1.33

import json
from typing import List, Tuple, Dict
import streamlit as st

st.set_page_config(page_title='AI Sourcing Assistant', layout='wide')

# ============================ Role Library (extensible) ============================
ROLE_LIB: Dict[str, Dict[str, List[str]]] = {
    'swe': {
        'titles': [
            'Software Engineer', 'Software Developer', 'SDE', 'SDE I', 'SDE II',
            'Senior Software Engineer', 'Full Stack Engineer', 'Backend Engineer',
            'Frontend Engineer', 'Platform Engineer'
        ],
        'must': ['python', 'java', 'go', 'microservices', 'distributed systems'],
        'nice': ['kubernetes', 'docker', 'graphql', 'gRPC', 'aws'],
    },
    'ml': {
        'titles': [
            'Machine Learning Engineer', 'ML Engineer', 'ML Scientist',
            'Applied Scientist', 'Data Scientist', 'AI Engineer'
        ],
        'must': ['python', 'pytorch', 'tensorflow', 'mlops', 'model deployment'],
        'nice': ['sklearn', 'xgboost', 'feature store', 'mlflow', 'sagemaker'],
    },
    'sre': {
        'titles': [
            'Site Reliability Engineer', 'SRE', 'Reliability Engineer',
            'DevOps Engineer', 'Platform Reliability Engineer'
        ],
        'must': ['kubernetes', 'terraform', 'prometheus', 'grafana', 'incident response'],
        'nice': ['golang', 'python', 'aws', 'gcp', 'oncall'],
    },
}

SMART_NOT = [
    'intern', 'internship', 'fellow', 'bootcamp', 'student', 'professor',
    'sales', 'marketing', 'hr', 'talent acquisition', 'recruiter',
    'customer support', 'help desk', 'desktop support', 'qa tester', 'graphic designer'
]

# ============================ Company Sets (top-tech + metros, editable) ============================
COMPANY_SETS: Dict[str, List[str]] = {
    'faang_plus': [
        'Google', 'Meta', 'Apple', 'Amazon', 'Netflix', 'Microsoft',
        'NVIDIA', 'Uber', 'Airbnb', 'Stripe', 'Dropbox', 'LinkedIn'
    ],
    'cloud_infra': [
        'AWS', 'Azure', 'Google Cloud', 'Cloudflare', 'Snowflake', 'Datadog',
        'Fastly', 'Akamai', 'HashiCorp', 'DigitalOcean', 'Twilio', 'MongoDB'
    ],
    'ai_first': [
        'OpenAI', 'Anthropic', 'DeepMind', 'Hugging Face', 'Stability AI',
        'Cohere', 'Scale AI', 'Character AI', 'Perplexity AI', 'xAI'
    ],
    'devtools_data': [
        'Databricks', 'Confluent', 'Elastic', 'Snyk', 'GitHub', 'GitLab',
        'JetBrains', 'CircleCI', 'PagerDuty', 'New Relic', 'Grafana Labs', 'Postman'
    ],
    'enterprise_saas': [
        'Salesforce', 'ServiceNow', 'Workday', 'Atlassian', 'Slack',
        'Notion', 'Asana', 'Zoom', 'Box', 'Dropbox'
    ],
    'consumer_social': [
        'YouTube', 'Instagram', 'WhatsApp', 'Snap', 'TikTok', 'Pinterest',
        'Reddit', 'Spotify', 'Discord'
    ],
    'fintech': [
        'Stripe', 'Square', 'Plaid', 'Coinbase', 'Robinhood', 'Brex',
        'Ramp', 'Affirm', 'Chime', 'SoFi'
    ],
    'marketplaces': [
        'Uber', 'Lyft', 'DoorDash', 'Instacart', 'Airbnb', 'Etsy',
        'Amazon Marketplace', 'Shopify'
    ],
    'high_growth': [
        'Rippling', 'Figma', 'Canva', 'Retool', 'Glean', 'Snowflake',
        'Databricks', 'Cloudflare', 'Notion', 'Scale AI'
    ],
}

METRO_COMPANIES: Dict[str, List[str]] = {
    'Any': [],
    'Bay Area': ['Google', 'Meta', 'Apple', 'Netflix', 'NVIDIA', 'Airbnb', 'Stripe', 'Uber', 'Databricks', 'Snowflake', 'DoorDash'],
    'New York': ['Google', 'Meta', 'Amazon', 'Spotify', 'Datadog', 'MongoDB', 'Ramp', 'Plaid', 'Etsy'],
    'Seattle': ['Amazon', 'Microsoft', 'AWS', 'Azure', 'Tableau'],
    'Remote-first': ['GitLab', 'Automattic', 'Zapier', 'Stripe', 'Dropbox', 'Doist'],
}

ROLE_TO_GROUPS: Dict[str, List[str]] = {
    'swe': ['faang_plus', 'devtools_data', 'enterprise_saas', 'cloud_infra', 'consumer_social', 'fintech', 'marketplaces', 'high_growth'],
    'ml':  ['ai_first', 'faang_plus', 'cloud_infra', 'devtools_data', 'enterprise_saas', 'consumer_social', 'high_growth'],
    'sre': ['cloud_infra', 'faang_plus', 'devtools_data', 'enterprise_saas', 'marketplaces', 'high_growth'],
}

# ============================ Synonyms (canonicalization) ============================
SYNONYMS: Dict[str, str] = {
    'golang': 'go',
    'k8s': 'kubernetes',
    'llm': 'large language model',
    'tf': 'tensorflow',
    'py': 'python',
}

# ============================ Helpers ============================

def unique_preserve(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        x2 = (x or '').strip()
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
        c = SYNONYMS.get((t or '').lower(), t or '').strip()
        k = c.lower()
        if k and k not in seen:
            seen.add(k)
            out.append(c)
    return out


def or_group(items: List[str]) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return ''
    quoted = []
    for i in items:
        if ' ' in i and not i.startswith('"'):
            quoted.append('"' + i + '"')
        else:
            quoted.append(i)
    return '(' + ' OR '.join(quoted) + ')'


def map_title_to_category(title: str) -> str:
    s = (title or '').lower()
    if any(t in s for t in ['sre', 'site reliability', 'reliab', 'devops', 'platform reliability']):
        return 'sre'
    if any(t in s for t in ['machine learning', 'ml engineer', 'applied scientist', 'data scientist', 'ai engineer', ' ml ', 'ml-', 'ml/']):
        return 'ml'
    return 'swe'


def expand_titles(base_titles: List[str], cat: str) -> List[str]:
    extra: List[str] = []
    if cat == 'swe':
        extra = ['Software Eng', 'Software Dev', 'Full-Stack Engineer', 'Backend Developer', 'Frontend Developer']
    elif cat == 'ml':
        extra = ['ML Eng', 'Machine Learning Specialist', 'Applied ML Engineer', 'ML Research Engineer']
    elif cat == 'sre':
        extra = ['Reliability Eng', 'DevOps SRE', 'Platform SRE', 'Production Engineer']
    return unique_preserve(base_titles + extra)


def build_keywords(must: List[str], nice: List[str], nots: List[str], qualifiers: List[str] = None) -> str:
    base = unique_preserve(must + nice + (qualifiers or []))
    core = or_group(base)
    if not core:
        return ''
    nots2 = unique_preserve(nots)
    if not nots2:
        return core
    return core + ' NOT (' + ' OR '.join(nots2) + ')'


def jd_extract(jd_text: str) -> Tuple[List[str], List[str], List[str]]:
    jd = (jd_text or '').lower()
    pool = set()
    for role in ROLE_LIB.values():
        for s in role['must'] + role['nice']:
            pool.add(s.lower())
    counts = {s: jd.count(s) for s in pool}
    ranked = [s for s, c in sorted(counts.items(), key=lambda x: x[1], reverse=True) if c > 0]
    must_ex = ranked[:8]
    nice_ex = ranked[8:16]
    auto_not = []
    for kw in ['intern', 'contract', 'temporary', 'help desk', 'desktop support', 'qa tester', 'graphic designer']:
        if kw in jd:
            auto_not.append(kw)
    return must_ex, nice_ex, auto_not


def string_health_report(s: str) -> List[str]:
    issues: List[str] = []
    if not s:
        return ['Keywords are empty — add must/nice skills.']
    if len(s) > 900:
        issues.append('Keywords look long (>900 chars); consider trimming.')
    if s.count(' OR ') > 80:
        issues.append('High OR count; remove niche/redundant terms.')
    depth = 0
    ok = True
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                ok = False
                break
    if depth != 0 or not ok:
        issues.append('Unbalanced parentheses; copy fresh strings or simplify.')
    return issues


def string_health_grade(s: str) -> str:
    if not s:
        return 'F'
    score = 100
    if len(s) > 900:
        score -= 25
    orc = s.count(' OR ')
    if orc > 80:
        score -= 25
    if orc > 40:
        score -= 15
    if any('Unbalanced parentheses' in x for x in string_health_report(s)):
        score -= 25
    return 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D' if score >= 60 else 'E' if score >= 50 else 'F'


def apply_seniority(titles: List[str], level: str) -> List[str]:
    base = []
    for t in titles:
        b = t
        for tok in ['Senior ', 'Staff ', 'Principal ', 'Lead ', 'Sr ']:
            b = b.replace(tok, '')
        base.append(b.strip())
    out: List[str] = []
    if level == 'All':
        out = titles + base
    elif level == 'Associate':
        out = ['Junior ' + b for b in base] + base
    elif level == 'Mid':
        out = base
    elif level == 'Senior+':
        out = ['Senior ' + b for b in base] + base
    else:
        out = ['Staff ' + b for b in base] + ['Principal ' + b for b in base] + ['Lead ' + b for b in base] + base
    seen, res = set(), []
    for x in out:
        xl = x.lower()
        if xl not in seen:
            seen.add(xl)
            res.append(x)
    return res[:24]

# ============================ Bright Theme CSS ============================
THEMES: Dict[str, Dict[str, str]] = {
    'Sky':   {'grad': 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)', 'bg': '#F8FAFC', 'card': '#FFFFFF', 'text': '#0F172A', 'muted': '#475569', 'ring': '#3B82F6', 'button': '#2563EB'},
    'Coral': {'grad': 'linear-gradient(135deg, #FB7185 0%, #F59E0B 100%)', 'bg': '#FFF7ED', 'card': '#FFFFFF', 'text': '#111827', 'muted': '#6B7280', 'ring': '#F97316', 'button': '#F97316'},
    'Mint':  {'grad': 'linear-gradient(135deg, #34D399 0%, #22D3EE 100%)', 'bg': '#ECFEFF', 'card': '#FFFFFF', 'text': '#0F172A', 'muted': '#334155', 'ring': '#10B981', 'button': '#10B981'},
}

def inject_css(theme_name: str) -> None:
    t = THEMES.get(theme_name, THEMES['Sky'])
    parts = []
    parts.append('<style>')
    parts.append(':root {')
    parts.append('--grad: ' + t['grad'] + ';')
    parts.append('--bg: ' + t['bg'] + ';')
    parts.append('--card: ' + t['card'] + ';')
    parts.append('--text: ' + t['text'] + ';')
    parts.append('--muted: ' + t['muted'] + ';')
    parts.append('--ring: ' + t['ring'] + ';')
    parts.append('--btn: ' + t['button'] + ';')
    parts.append('--gap: 16px;')
    parts.append('--pad: 14px;')
    parts.append('--radius: 16px;')
    parts.append('--codefs: 12.5px;')
    parts.append('--btnpad: 9px 14px;')
    parts.append('}')
    parts.append(".stApp, [data-testid='stAppViewContainer'] {background: var(--bg); color: var(--text);}")
    parts.append("[data-testid='stHeader'] {background: transparent;}")
    parts.append(".hero {padding: var(--pad); border-radius: var(--radius); background: var(--card); ")
    parts.append("border: 1px solid rgba(0,0,0,.06); box-shadow: 0 6px 24px rgba(2,6,23,.06); margin-bottom: var(--gap);}")
    parts.append(".hero h1 {margin: 0; font-size: 28px; font-weight: 800; background: var(--grad); ")
    parts.append("-webkit-background-clip: text; background-clip: text; color: transparent;}")
    parts.append(".chips {display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px;}")
    parts.append(".chip {padding: 6px 10px; border-radius: 999px; font-size: 12px; color: var(--text); ")
    parts.append("background: rgba(2,6,23,.04); border: 1px solid rgba(2,6,23,.06);}")
    parts.append("input[type='text'], textarea {background: var(--card) !important; color: var(--text) !important; ")
    parts.append("border: 1px solid rgba(2,6,23,.08) !important; border-radius: var(--radius) !important;}")
    parts.append("input[type='text']:focus, textarea:focus {outline: none !important; border-color: var(--ring) !important; ")
    parts.append("box-shadow: 0 0 0 3px rgba(37,99,235,.18) !important;}")
    parts.append(".stButton>button, .stDownloadButton>button {background: var(--btn); color: #FFFFFF; font-weight: 700; border: none; ")
    parts.append("padding: var(--btnpad); border-radius: 999px; box-shadow: 0 10px 24px rgba(2,6,23,.12);}")
    parts.append(".stButton>button:hover, .stDownloadButton>button:hover {filter: brightness(1.05);}")
    parts.append(".stButton>button:focus {outline: none; box-shadow: 0 0 0 3px rgba(37,99,235,.25);}")
    parts.append('pre, code {font-size: var(--codefs) !important;}')
    parts.append(".grid {display: grid; gap: var(--gap); grid-template-columns: repeat(12, 1fr);}")
    parts.append(".card {grid-column: span 6; background: var(--card); border: 1px solid rgba(2,6,23,.06); ")
    parts.append("border-radius: var(--radius); padding: var(--pad); box-shadow: 0 6px 24px rgba(2,6,23,.06);}")
    parts.append(".hint {font-size: 12px; color: var(--muted); margin-top: 4px;}")
    parts.append(".divider {height: 1px; background: linear-gradient(90deg, transparent, rgba(2,6,23,.15), transparent); margin: 8px 0;}")
    parts.append(".sticky {position: fixed; left: 0; right: 0; bottom: 12px; z-index: 9999; display:flex; gap:8px; justify-content:center;}")
    parts.append(".sticky .btn {background: var(--btn); color:#fff; padding:8px 12px; border-radius:999px; font-weight:700; border:none;}")
    parts.append('</style>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


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
        st.markdown("<div class='chips'>" + ''.join(chips) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Assistant Panels (tabs)
    st.subheader("📚 Assistant Panels")
    tabs = st.tabs(["🧠 Role Intel","🌐 Signals","🏢 Company Maps","🚦 Filters","💌 Outreach","✅ Checklist","⬇️ Export"])
    with tabs[0]:
        st.markdown("**What this shows:** quick context for the role, common responsibilities, and what *not* to target.")
        if category == "ml":
            st.markdown("- **Focus:** production ML (training → deployment), feature pipelines, model monitoring.
- **Common stacks:** Python, PyTorch/TensorFlow, Airflow, MLflow/Feature Store, AWS/GCP.
- **Avoid:** pure research-only profiles when you need prod ML; BI/marketing analysts.")
        elif category == "sre":
            st.markdown("- **Focus:** reliability, incident response, infra as code, observability.
- **Common stacks:** Kubernetes, Terraform, Prometheus/Grafana, Go/Python, AWS/GCP.
- **Avoid:** Help Desk/IT support, QA-only.")
        else:
            st.markdown("- **Focus:** building services and features, code quality, scalability.
- **Common stacks:** Python/Java/Go, microservices, Docker/Kubernetes, AWS/GCP.
- **Avoid:** QA-only, desktop support.")
        st.markdown("**Title synonyms:**")
        st.code("
".join(titles), language="text")
        st.markdown("**Top skills:**")
        st.code(", ".join(unique_preserve(must + nice)) or "python, java, go", language="text")
    with tabs[1]:
        st.markdown("**What this shows:** quick levers to tighten or widen results based on signal strength.")
        st.markdown("- Use **Title (Current)** first; if low volume, add **Title (Past)**.
- Start with **Keywords** then add/remove 2–3 skills to control volume.
- Add **NOT** terms like `intern, help desk, QA` to reduce noise.")
        st.markdown("**Your current NOT terms:**")
        st.code(", ".join(all_not) or "intern, internship, help desk", language="text")
    with tabs[2]:
        st.markdown("**What this shows:** companies that commonly employ this role. Paste into Company filters or use as a target list.")
        st.code(companies_or or "(\"Google\" OR \"Meta\")", language="text")
        st.markdown("**List view:**")
        st.write(companies or ["Google","Meta","Amazon"])
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
        st.write(filt or ["Seniority: Any","Company size: Any"])
        st.markdown("**Tip:** If volume is high, add `current company = any` and rely on Titles + Keywords.")
    with tabs[4]:
        st.markdown("**What this shows:** 2 short, friendly outreach drafts you can personalize and send fast.")
        outreach_a = """Subject: {role} impact at {your_company}

Hi {{name}},
I’m hiring for a {role} to build {{impact area}}. Your background with {{relevant tech}} stood out. Interested in a quick chat?
— {{recruiter}}""".format(role=st.session_state.get("role_title",""), your_company="our team")
        outreach_b = """Subject: {role} — fast chat?

Hi {{name}},
We’re scaling {{team/product}}. Your experience across {skills} looks like a great fit. 15 mins to explore?
— {{recruiter}}""".format(role=st.session_state.get("role_title",""), skills=", ".join(must[:5]) or "backend, infra")
        st.code(outreach_a, language="text")
        st.code(outreach_b, language="text")
    with tabs[5]:
        st.markdown("**What this shows:** a quick start checklist to de-risk your search.")
        st.markdown("- Confirm role scope & must-haves with hiring manager.
- Align on 3–5 anchor companies to target first.
- Decide precision vs coverage strategy.
- Save the search; schedule a daily review.")
    with tabs[6]:
        st.markdown("**What this shows:** the same export pack as below, for convenience.")
        st.code(pack_text, language="text")


def code_card(title: str, text: str, hint: str = '') -> None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;font-size:14px;color:var(--muted);'>" + title + "</h3>", unsafe_allow_html=True)
    st.code(text or '', language='text')
    if hint:
        st.markdown("<div class='hint'>" + hint + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ============================ URL State ============================
qp = st.query_params

def qp_get(name: str, default: str = '') -> str:
    val = qp.get(name, None)
    if val is None:
        return default
    if isinstance(val, list):
        return val[0] if val else default
    return val or default


def qp_set(**kwargs):
    qp.clear()
    for k, v in kwargs.items():
        qp[k] = v

# ============================ UI: Inputs ============================
col_theme = st.columns([1])[0]
with col_theme:
    theme_choice = st.selectbox('Theme', list(THEMES.keys()), index=[*THEMES].index(qp_get('theme', 'Sky')))
inject_css(theme_choice)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
left, right = st.columns([3, 2])
with left:
    job_title = st.text_input('Search by job title', value=qp_get('title', ''), placeholder='e.g., Staff Machine Learning Engineer')
with right:
    location = st.text_input('Location (optional)', value=qp_get('loc', ''), placeholder='e.g., New York, Remote, Bay Area')

extra_not = st.text_input('Extra NOT terms (comma-separated, optional)', value=qp_get('not', ''), placeholder='e.g., contractor, internship')

col1, col2, col3, col4 = st.columns(4)
with col1:
    level = st.selectbox('Seniority', ['All', 'Associate', 'Mid', 'Senior+', 'Staff/Principal'], index=['All','Associate','Mid','Senior+','Staff/Principal'].index(qp_get('level', 'All')))
with col2:
    env = st.selectbox('Work setting', ['Any', 'On-site', 'Hybrid', 'Remote'], index=['Any','On-site','Hybrid','Remote'].index(qp_get('env', 'Any')))
with col3:
    size = st.selectbox('Company size', ['Any', 'Startup', 'Growth', 'Enterprise'], index=['Any','Startup','Growth','Enterprise'].index(qp_get('size', 'Any')))
with col4:
    metro = st.selectbox('Metro focus', list(METRO_COMPANIES.keys()), index=list(METRO_COMPANIES.keys()).index(qp_get('metro', 'Any')))

# Build
if st.button('✨ Build sourcing pack') and (job_title or '').strip():
    qp_set(title=job_title, loc=location, level=level, env=env, size=size, metro=metro, theme=theme_choice)
    st.session_state['built'] = True
    st.session_state['role_title'] = job_title
    st.session_state['location'] = location
    st.session_state['category'] = map_title_to_category(job_title)

    # Default packs from ontology only (no external AI)
    R = ROLE_LIB[st.session_state['category']]
    titles_seed = expand_titles(R['titles'], st.session_state['category'])
    must_seed = list(R['must'])
    nice_seed = list(R['nice'])
    not_seed = list(SMART_NOT)

    st.session_state['titles'] = titles_seed
    st.session_state['must'] = must_seed
    st.session_state['nice'] = nice_seed
    st.session_state['not_terms'] = not_seed

category = st.session_state.get('category', '')
hero(st.session_state.get('role_title', ''), category, st.session_state.get('location', ''))

if st.session_state.get('built'):
    titles = st.session_state.get('titles', [])
    must = st.session_state.get('must', [])
    nice = st.session_state.get('nice', [])
    base_not = st.session_state.get('not_terms', [])

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Auto-infer seniority from title text (light heuristic)
    title_lower = (st.session_state.get('role_title', '') or '').lower()
    if any(w in title_lower for w in ['staff', 'principal']):
        level = 'Staff/Principal'
    elif any(w in title_lower for w in ['senior', 'sr ']):
        level = 'Senior+'

    # Seniority adjustment affects title set for LinkedIn title fields
    titles = apply_seniority(titles, level)

    # Editors (always visible)
    st.subheader('✏️ Customize')
    c1, c2 = st.columns([1, 1])
    with c1:
        newline = chr(10)
        titles_default = newline.join(titles)
        titles_text = st.text_area('Titles (one per line)', value=titles_default, height=180)
    with c2:
        comma_space = chr(44) + chr(32)
        must_default = comma_space.join(must)
        must_text = st.text_area('Must-have skills (comma-separated)', value=must_default, height=120)
        nice_default = comma_space.join(nice)
        nice_text = st.text_area('Nice-to-have skills (comma-separated)', value=nice_default, height=120)

    # JD extraction (optional)
    with st.expander('📄 Paste JD → Auto-extract (optional)'):
        jd = st.text_area('Paste JD (optional)', height=160)
        if st.button('Extract from JD'):
            m_ex, n_ex, n_not = jd_extract(jd)
            applied = False
            if m_ex:
                must = unique_preserve(m_ex + must); applied = True
            if n_ex:
                nice = unique_preserve(n_ex + nice); applied = True
            if n_not:
                base_not = unique_preserve(base_not + n_not); applied = True
            if applied:
                st.success('JD terms applied.')
            if not st.session_state.get('built'):
    st.info("Type a job title (try 'Staff Machine Learning Engineer'), pick a bright theme, then click **Build sourcing pack**.")
