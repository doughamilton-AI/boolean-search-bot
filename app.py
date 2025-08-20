# app.py — Minimal, Accurate, AI‑powered Sourcing Assistant
# Requirements (put these lines into requirements.txt):
# streamlit>=1.33
# openai>=1.85.0

import os, re
import json
from typing import List, Dict, Optional
import streamlit as st

st.set_page_config(page_title="AI Sourcing Assistant", layout="wide")

# ============================ Small Canon + Synonyms (post‑processing) ============================
SYNONYMS: Dict[str, str] = {
    'golang': 'go',
    'k8s': 'kubernetes',
    'llm': 'large language model',
    'tf': 'tensorflow',
    'py': 'python',
}

# Fallback seeds if AI is unavailable
SEEDS: Dict[str, Dict[str, List[str]]] = {
    'swe': {
        'titles': ['Software Engineer','Senior Software Engineer','Backend Engineer','Frontend Engineer','Full Stack Engineer','Platform Engineer'],
        'must': ['python','java','go','distributed systems','microservices'],
        'nice': ['kubernetes','docker','graphql','gRPC','aws'],
        'not':  ['intern','internship','qa tester','help desk','desktop support']
    },
    'ml': {
        'titles': ['Machine Learning Engineer','Senior Machine Learning Engineer','Applied Scientist','ML Engineer','AI Engineer','Data Scientist'],
        'must': ['python','pytorch','tensorflow','mlops','model deployment'],
        'nice': ['sklearn','xgboost','feature store','mlflow','sagemaker'],
        'not':  ['intern','analyst (marketing)','biostatistics internship','qa tester']
    },
    'sre': {
        'titles': ['Site Reliability Engineer','SRE','Reliability Engineer','DevOps Engineer','Platform Reliability Engineer'],
        'must': ['kubernetes','terraform','prometheus','grafana','incident response'],
        'nice': ['golang','python','aws','gcp','oncall'],
        'not':  ['help desk','desktop support','qa tester','field technician']
    }
}

# ============================ Helper functions ============================

def unique_preserve(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        s = (x or '').strip()
        if not s:
            continue
        k = s.lower()
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def canonicalize(seq: List[str]) -> List[str]:
    out: List[str] = []
    for t in seq:
        s = (t or '').strip()
        if not s:
            continue
        out.append(SYNONYMS.get(s.lower(), s))
    return unique_preserve(out)


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


def build_keywords(must: List[str], nice: List[str], not_terms: List[str]) -> str:
    core = or_group(unique_preserve(must + nice))
    if not core:
        return ''
    nts = unique_preserve(not_terms)
    if nts:
        return core + ' NOT (' + ' OR '.join(nts) + ')'
    return core


def map_family(title: str) -> str:
    s = (title or '').lower()
    if any(x in s for x in ['site reliability','sre','reliab','devops']):
        return 'sre'
    if any(x in s for x in ['machine learning','ml engineer','applied scientist','ai engineer']):
        return 'ml'
    return 'swe'

# ============================ OpenAI (Structured Output) ============================

def get_openai_client() -> Optional["OpenAI"]:
    """Create an OpenAI client using key from Streamlit Secrets or env.
    Supports optional org/project if provided in secrets or env.
    """
    key = None
    # Prefer Streamlit secrets
    try:
        if 'OPENAI_API_KEY' in st.secrets:
            key = st.secrets['OPENAI_API_KEY']
    except Exception:
        key = None
    # Fallback to env var
    if not key:
        key = os.getenv('OPENAI_API_KEY')
    if not key:
        return None

    # Optional org/project
    org = None
    proj = None
    try:
        org = st.secrets.get('OPENAI_ORG_ID', None) if hasattr(st, 'secrets') else None
        proj = st.secrets.get('OPENAI_PROJECT', None) if hasattr(st, 'secrets') else None
    except Exception:
        org = org or os.getenv('OPENAI_ORG_ID')
        proj = proj or os.getenv('OPENAI_PROJECT')
    org = org or os.getenv('OPENAI_ORG_ID')
    proj = proj or os.getenv('OPENAI_PROJECT')

    try:
        from openai import OpenAI  # type: ignore
        # Only pass org/project if present (older SDKs accept them as kwargs)
        kwargs = {'api_key': key}
        if org:
            kwargs['organization'] = org
        if proj:
            kwargs['project'] = proj
        return OpenAI(**kwargs)
    except Exception:
        return None

# Helpers to mask keys and sanitize error strings

def _mask_key(k: Optional[str]) -> str:
    if not k:
        return 'not found'
    k = str(k)
    if len(k) <= 10:
        return '******'
    return f"{k[:7]}…{k[-4:]} (len {len(k)})"


def _get_key_source_and_preview() -> str:
    src = 'none'
    k = None
    try:
        if 'OPENAI_API_KEY' in st.secrets:
            src = 'secrets'
            k = st.secrets['OPENAI_API_KEY']
    except Exception:
        pass
    if src == 'none' and os.getenv('OPENAI_API_KEY'):
        src = 'env'
        k = os.getenv('OPENAI_API_KEY')
    return f"source={src} • key={_mask_key(k)}"


def _sanitize_err(msg: str) -> str:
    # Mask any embedded keys like sk-xxxxx
    return re.sub(r"sk-[A-Za-z0-9_\-]+", "sk-****", msg or "")



def call_openai_pack(client, model: str, job_title: str, job_desc: str, location: str, mode: str) -> Dict:
    """Return dict with keys: titles.must, titles.variants, skills.must, skills.nice, not_terms, companies.
       On any failure, return {} (caller will fall back)."""
    if client is None:
        return {}

    schema: Dict = {
        'type': 'object',
        'properties': {
            'titles': {
                'type': 'object',
                'properties': {
                    'must': {'type': 'array','items': {'type':'string'}},
                    'variants': {'type': 'array','items': {'type':'string'}}
                },
                'required': ['must','variants'],
                'additionalProperties': False
            },
            'skills': {
                'type': 'object',
                'properties': {
                    'must': {'type': 'array','items': {'type':'string'}},
                    'nice': {'type': 'array','items': {'type':'string'}}
                },
                'required': ['must','nice'],
                'additionalProperties': False
            },
            'not_terms': {'type': 'array','items': {'type':'string'}},
            'companies': {'type': 'array','items': {'type':'string'}},
        },
        'required': ['titles','skills','not_terms','companies'],
        'additionalProperties': False
    }

    joiner = chr(10)
    system_prompt = joiner.join([
        'You are an expert technical sourcer for top tech.',
        'Return JSON ONLY that matches the provided schema exactly.',
        'Prefer canonical skills; avoid buzzwords. Be concise and accurate.',
        'If uncertain, prefer higher precision over coverage.'
    ])

    caps = {'mode': mode, 'titles': 18 if mode=='precision' else 24, 'skills': 24 if mode=='coverage' else 16}
    context = {'synonyms': SYNONYMS, 'caps': caps}

    user_prompt = joiner.join([
        'JOB_TITLE: ' + (job_title or ''),
        'LOCATION: ' + (location or ''),
        'MODE: ' + mode,
        'JD:' + joiner + ((job_desc or '').strip() or '(none)'),
        'CONTEXT:' + joiner + json.dumps(context, ensure_ascii=True)
    ])

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2 if mode=='precision' else 0.3,
            messages=[{'role':'system','content':system_prompt}, {'role':'user','content':user_prompt}],
            response_format={'type':'json_schema','json_schema': {'name':'SourcingPack','schema':schema,'strict':True}}
        )
        content = resp.choices[0].message.content or '{}'
        return json.loads(content)
    except Exception:
        return {}

# ============================ UI ============================

st.markdown('<h1 style="margin:0">AI Sourcing Assistant</h1>', unsafe_allow_html=True)
st.caption('Type a role title, optionally paste a JD, then click Build. You will get LinkedIn‑ready Title, Keywords, and Company strings.')

client = get_openai_client()

colA, colB = st.columns([2, 3])
with colA:
    title_in = st.text_input('Role title', placeholder='e.g., Senior Machine Learning Engineer')
    mode = st.radio('Search style', ['precision','coverage'], index=0, horizontal=True, help='Precision = fewer, higher‑signal. Coverage = broader mapping.')
    loc_in = st.text_input('Location (optional)', placeholder='e.g., Bay Area, NYC, Remote')
    model_choice = st.selectbox('Model', ['gpt-4o-mini','gpt-4o'], index=0, help='Choose a model you have access to.')
    col_btn1, col_btn2 = st.columns([1,1])
    with col_btn1:
        build = st.button('✨ Build with AI')
    with col_btn2:
        test_ai = st.button('Test AI connection')
with colB:
    jd_in = st.text_area('Paste job description (optional)', height=170)

if test_ai:
    if client is None:
        st.error('No OpenAI key detected. Add OPENAI_API_KEY in Streamlit Secrets or environment.')
    else:
        # Show SDK version + model, and surface the actual exception to help debugging
        try:
            import importlib.metadata as md
            ver = md.version('openai')
        except Exception:
            ver = 'unknown'
        st.caption(f"OpenAI SDK version: {ver} • Model: {model_choice}")
        st.caption(_get_key_source_and_preview())
        try:
            ping_schema = {
                'type': 'object',
                'properties': {'ok': {'type': 'boolean'}},
                'required': ['ok'],
                'additionalProperties': False
            }
            resp = client.chat.completions.create(
                model=model_choice,
                temperature=0,
                messages=[
                    {'role': 'system', 'content': 'Return JSON only that matches the schema.'},
                    {'role': 'user', 'content': '{"ok": true}'}
                ],
                response_format={'type': 'json_schema', 'json_schema': {'name': 'Ping', 'schema': ping_schema, 'strict': True}}
            )
            _ = json.loads(resp.choices[0].message.content or '{}')
            st.success('✅ AI connection looks good. Model responded.')
        except Exception as e:
            st.error(f"❌ AI test failed: {type(e).__name__}: {_sanitize_err(str(e))}")

if build and (title_in or '').strip():
    fam = map_family(title_in)
    out = call_openai_pack(client, model_choice, title_in, jd_in, loc_in, mode)

    # Auto-fallback to another model if the chosen one fails
    if not out and client is not None:
        alt_model = 'gpt-4o' if model_choice != 'gpt-4o' else 'gpt-4o-mini'
        try_alt = call_openai_pack(client, alt_model, title_in, jd_in, loc_in, mode)
        if try_alt:
            st.info(f"Primary model '{model_choice}' failed; used '{alt_model}' instead.")
            out = try_alt

    if not out:
        seed = SEEDS[fam]
        titles = seed['titles']
        must = seed['must']
        nice = seed['nice']
        not_terms = seed['not']
        companies = ['Google','Meta','Apple','Amazon','Microsoft','NVIDIA','Stripe','Airbnb','Uber','Dropbox','LinkedIn']
        st.info('AI not available — using a solid fallback pack.')
    else:
        titles = canonicalize((out.get('titles',{}).get('must',[]) or []) + (out.get('titles',{}).get('variants',[]) or []))
        must = canonicalize(out.get('skills',{}).get('must',[]) or [])
        nice = canonicalize(out.get('skills',{}).get('nice',[]) or [])
        not_terms = canonicalize(out.get('not_terms',[]) or [])
        companies = canonicalize(out.get('companies',[]) or [])

    # Cap sizes by mode
    if mode == 'precision':
        titles = titles[:12]; must = must[:12]; nice = nice[:6]; not_terms = not_terms[:8]; companies = companies[:24]
    else:
        titles = titles[:22]; must = must[:18]; nice = nice[:10]; not_terms = not_terms[:12]; companies = companies[:30]

    # Build blocks
    title_current = or_group(titles)
    title_past = or_group(titles[:min(20, len(titles))])
    keywords = build_keywords(must, nice, not_terms)
    companies_or = or_group(companies)

    # Render (copy‑friendly)
    st.subheader('Results')
    st.markdown('**Title (Current) — paste into LinkedIn ▸ People ▸ Title (Current)**')
    st.code(title_current or '("Software Engineer")', language='text')

    st.markdown('**Title (Past) — paste into LinkedIn ▸ People ▸ Title (Past)**')
    st.code(title_past or '("Software Engineer")', language='text')

    st.markdown('**Keywords (Boolean) — paste into LinkedIn ▸ People ▸ Keywords**')
    st.code(keywords or '(python OR java) NOT (intern OR "help desk")', language='text')

    st.markdown('**Companies (OR) — paste into LinkedIn ▸ People ▸ Current/Past company**')
    st.code(companies_or or '("Google" OR "Meta")', language='text')

    # Simple download
    lines: List[str] = []
    lines.append('ROLE: ' + (title_in or ''))
    lines.append('LOCATION: ' + (loc_in or ''))
    lines.append('')
    lines.append('TITLE (CURRENT):')
    lines.append(title_current)
    lines.append('')
    lines.append('TITLE (PAST):')
    lines.append(title_past)
    lines.append('')
    lines.append('KEYWORDS:')
    lines.append(keywords)
    lines.append('')
    lines.append('COMPANIES (OR):')
    lines.append(companies_or)
    pack_text = (chr(10)).join(lines)
    st.download_button('Download pack (.txt)', data=pack_text, file_name='sourcing_pack.txt')
else:
    st.info('Enter a role title, optionally paste a JD, pick a model, then click Build with AI.')
