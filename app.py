# AI Sourcing Assistant


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
from urllib.parse import urlencode, quote_plus

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

# ============================= Global skill dictionary (extra coverage) =============================
GLOBAL_SKILLS_EXTRA = [
    # SWE / Backend core
    "microservices","distributed systems","rest","grpc","graphql","event-driven","cqrs","api design","openapi","swagger",
    "message queue","kafka","pulsar","rabbitmq","nats","kinesis","sqs","pub/sub","serverless","lambda",
    "oauth2","oidc","sso","auth0","okta","jwt","rate limiting","caching","feature flags",
    # Infra / DevOps / SRE
    "docker","containerd","kubernetes","k8s","helm","kustomize","istio","linkerd","envoy","service mesh",
    "terraform","pulumi","ansible","packer","argo cd","spinnaker","jenkins","github actions","gitlab ci","circleci","bazel","nix",
    "prometheus","grafana","opentelemetry","jaeger","datadog","new relic","splunk","pagerduty","oncall","incident response","slo","sla","observability",
    "s3","gcs","cloud storage","cloudfront","cloudflare",
    # Data Eng / Platform
    "spark","flink","beam","kafka streams","dbt","airflow","dagster","orchestration",
    "parquet","avro","delta lake","iceberg","hudi","lakehouse",
    "snowflake","redshift","bigquery","presto","trino","hive","clickhouse",
    # Databases / Caches / Search
    "postgres","mysql","mariadb","sqlite","redis","memcached","mongo","cassandra","dynamodb","bigtable",
    "elasticsearch","opensearch","timescaledb","influxdb","neo4j","graph db",
    # ML / AI
    "llm","large language model","transformer","bert","gpt","rag","retrieval augmented generation","vector db",
    "embeddings","tokenization","sentence transformers","langchain","llamaindex",
    "faiss","pinecone","weaviate","milvus","chroma",
    "pytorch","tensorflow","sklearn","xgboost","lightgbm","catboost","onnx","torchserve","triton",
    "mlflow","kubeflow","sagemaker","ray","feature store","feast",
    # Analytics
    "experimentation","a/b testing","ab testing","causal inference","sql window functions","cohort analysis","retention","funnel analysis",
    # Frontend
    "next.js","vue","angular","svelte","redux","rtk","rtk query","zustand","mobx","rxjs","webpack","vite",
    "jest","testing library","cypress","playwright","storybook","tailwindcss","scss","sass","css modules","a11y","accessibility","ssr","isr",
    # iOS / Android
    "swift","swiftui","combine","uikit","objective-c","cocoapods","carthage","spm","alamofire","mvvm","xcuitest",
    "kotlin","java","jetpack compose","coroutines","flow","dagger","hilt","koin","retrofit","room","espresso",
    # Security
    "owasp","sast","dast","sca","threat modeling","pentest","bug bounty","semgrep","burp suite","zap",
    "iam","kms","secrets management","vault","mfa","zero trust","saml","oauth2","oidc",
]

# Canonicalize common synonyms and spelling variants used across company JDs
CANON_SKILLS = {
    # languages & runtimes
    "golang":"go","go lang":"go","nodejs":"node","node.js":"node","c sharp":"c#","c plus plus":"c++",
    # k8s & infra
    "k8s":"kubernetes","eks":"kubernetes","gke":"kubernetes","aks":"kubernetes","argocd":"argo cd","argo-cd":"argo cd",
    "ci/cd":"cicd","ci-cd":"cicd",
    # api & auth
    "oauth 2.0":"oauth2","open telemetry":"opentelemetry","o11y":"observability",
    # data / lakehouse
    "delta":"delta lake","apache iceberg":"iceberg",
    # ml/ai
    "large language model":"llm","retrieval augmented generation":"rag","vector database":"vector db",
    # frontend
    "redux toolkit":"rtk","rtk-query":"rtk query","tailwind":"tailwindcss",
    # misc
    "micro services":"microservices","micro-services":"microservices","SRE":"sre"
}

SMART_EXCLUDE_BASE = [
    "intern", "internship", "fellow", "bootcamp", "student", "professor",
    "sales", "marketing", "hr", "talent acquisition", "recruiter",
    "customer support", "qa tester", "help desk", "desktop support",
]

# Query param helpers (share/load)

def _get_query_params_compat():
    try:
        return dict(st.query_params)
    except Exception:
        try:
            return st.experimental_get_query_params()
        except Exception:
            return {}

def _init_from_query_params():
    if st.session_state.get("built"):
        return
    qp = _get_query_params_compat()
    if not qp:
        return
    def _p(key, default=""):
        v = qp.get(key, default)
        if isinstance(v, list):
            return v[0] if v else default
        return v
    role = _p("role", "")
    cat = _p("cat", "")
    titles = [t for t in _p("titles", "").split("|") if t]
    must = [s.strip() for s in _p("must", "").split(",") if s.strip()]
    nice = [s.strip() for s in _p("nice", "").split(",") if s.strip()]
    nots = [s.strip() for s in _p("not", "").split(",") if s.strip()]
    extras = [s for s in _p("extras", "").split("|") if s]
    include_extras = _p("inc", "0") == "1"
    loc = _p("loc", "")
    if role or titles or must or nice:
        if not cat:
            cat = map_title_to_category_any(role)
        st.session_state["built"] = True
        st.session_state["any_title"] = role
        st.session_state["location"] = loc
        st.session_state["cat"] = cat
        base_titles = ROLE_LIB.get(cat, {}).get("titles", [])
        st.session_state["edited_titles"] = titles or expand_titles(base_titles, cat)
        st.session_state["edited_must"] = must or ROLE_LIB.get(cat, {}).get("must", [])
        st.session_state["edited_nice"] = nice or ROLE_LIB.get(cat, {}).get("nice", [])
        st.session_state["selected_extras"] = extras
        st.session_state["include_extras_core"] = include_extras
        st.session_state["jd_not"] = nots

# ============================= Helpers =============================

def _sanitize_for_linkedin(s: str) -> str:
    """Make a boolean string safer for LinkedIn's URL search box using code-point mappings (no fragile quotes)."""
    s = s or ""
    # Replace newline/carriage returns with spaces
    s = s.replace("
", " ").replace("
", " ")
    # Normalize curly punctuation to ASCII using Unicode code points (avoids broken string literals)
    trans = {
        0x2014: "-",   # — em dash
        0x2013: "-",   # – en dash
        0x201C: '"',   # “ left dbl quote
        0x201D: '"',   # ” right dbl quote
        0x2018: "'",   # ‘ left single quote
        0x2019: "'",   # ’ right single quote
        0x2026: "...", # … ellipsis
    }
    s = s.translate(trans)
    # Collapse whitespace
    s = " ".join(s.split())
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

# Initialize from share link if present
_init_from_query_params()

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
    jd_not_terms = st.session_state.get("jd_not", [])
    nots = SMART_EXCLUDE_BASE + R.get("false_pos", []) + jd_not_terms + [t.strip() for t in (extra_not or "").split(",") if t.strip()]
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
        # ---- 📄 Paste JD → Auto-extract ----
        with st.expander("📄 Paste Job Description → Auto-extract", expanded=False):
            jd_text = st.text_area("Paste the full JD (optional)", height=220, placeholder="Paste the role's Responsibilities/Requirements/Preferred sections here…")
            if st.button("Extract from JD", key="extract_jd"):
                # Simple extraction based on global skills frequency; prioritizes 'requirements' terms
                def _flatten_role_lib():
                    skills = set()
                    for v in ROLE_LIB.values():
                        for k in ("must","nice","frameworks","clouds","databases"):
                            skills.update(v.get(k, []))
                    return sorted(skills)
                GLOBAL_SKILLS = _flatten_role_lib()
                # include global extras
                GLOBAL_SKILLS = sorted(set(GLOBAL_SKILLS) | set(GLOBAL_SKILLS_EXTRA))
                # canonicalize common variants
                CANON = CANON_SKILLS
                text = (jd_text or "").lower()
                # fast not-term detection
                auto_not = []
                for kw in ["intern","internship","contract","temporary","unpaid","help desk","desktop support","qa tester","graphic designer","sales","marketing"]:
                    if kw in text: auto_not.append(kw)
                tokens = re.findall(r"[a-zA-Z0-9+#\.\-/]+", text)
                def canon(tok: str) -> str:
                    t = tok.lower().replace("_"," ").replace("-"," ")
                    t = CANON.get(t, t)
                    return t
                norm = [canon(t) for t in tokens]
                counts = {s:0 for s in GLOBAL_SKILLS}
                for s in GLOBAL_SKILLS:
                    c = canon(s)
                    # phrase or special-char skills: count in full text
                    if (" " in c) or any(ch in c for ch in ["#","+",".","-","/"]):
                        counts[s] = len(re.findall(re.escape(c), text))
                    else:
                        counts[s] = norm.count(c)
                ranked = [s for s,_c in sorted(counts.items(), key=lambda x: x[1], reverse=True) if _c>0]
                must_ex = ranked[:8]
                nice_ex = ranked[8:16]
                st.session_state["edited_must"] = must_ex or st.session_state.get("edited_must", [])
                st.session_state["edited_nice"] = nice_ex or st.session_state.get("edited_nice", [])
                # keep titles from current category, but allow "Senior" if present
                add_senior = any(w in text for w in ["senior","staff","principal","lead"])
                base_titles = st.session_state.get("edited_titles", [])
                if add_senior and base_titles:
                    enriched = []
                    for t in base_titles:
                        if not t.lower().startswith("senior ") and "Senior" in t:
                            enriched.append(t)
                        enriched.append(t)
                    st.session_state["edited_titles"] = list(dict.fromkeys(enriched))
                st.session_state["jd_not"] = list(dict.fromkeys(st.session_state.get("jd_not", []) + auto_not))
                _safe_rerun()

        # ---- Refresh from session (so JD extract applies without rerun) ----
        titles = st.session_state.get("edited_titles", titles)
        must = st.session_state.get("edited_must", must)
        nice = st.session_state.get("edited_nice", nice)
        selected_extras = st.session_state.get("selected_extras", selected_extras)
        include_extras_core = st.session_state.get("include_extras_core", include_extras_core)
        if st.session_state.pop("just_extracted", False):
            st.success("Extracted skills from JD and applied ✅")

        # ---- Seniority pills (adjust Title sets & show LI guidance) ----
        def _apply_seniority(titles_in: List[str], level: str) -> List[str]:
            # Remove existing seniority words to form base
            base = []
            for t in titles_in:
                b = t
                for tok in ["Senior ", "Staff ", "Principal ", "Lead ", "Sr "]:
                    b = b.replace(tok, "")
                base.append(b.strip())
            # Build per level
            if level == "All levels":
                out = titles_in + base
            elif level == "Associate":
                out = [f"Junior {b}" for b in base] + base
            elif level == "Mid":
                out = base
            elif level == "Senior+":
                out = [f"Senior {b}" for b in base] + base
            else:  # Staff/Principal
                out = [f"Staff {b}" for b in base] + [f"Principal {b}" for b in base] + [f"Lead {b}" for b in base] + base
            # dedupe, keep order
            seen, res = set(), []
            for x in out:
                xl = x.lower()
                if xl not in seen:
                    seen.add(xl); res.append(x)
            return res[:24]

        col_sv1, col_sv2 = st.columns([2,3])
        with col_sv1:
            seniority_level = st.radio("Seniority focus", ["All levels","Associate","Mid","Senior+","Staff/Principal"], horizontal=True, index=0)
        with col_sv2:
            st.caption("These pills reshape Title sets and inform Years of experience/Seniority you’ll pick in LinkedIn.")
        titles = _apply_seniority(titles, seniority_level)

        # Build strings now, after any JD extraction/edits/seniority
        li_title = or_group(titles)
        core_terms = must + nice + (selected_extras if include_extras_core else [])
        li_kw_core = or_group(core_terms)
        jd_not_terms = st.session_state.get("jd_not", [])
        nots = SMART_EXCLUDE_BASE + R.get("false_pos", []) + jd_not_terms + [t.strip() for t in (extra_not or "").split(",") if t.strip()]
        li_keywords = f"{li_kw_core} NOT (" + " OR ".join(nots) + ")" if nots else li_kw_core
        expanded_keywords = build_expanded_keywords(must, nice, R.get("frameworks", []), R.get("clouds", []), R.get("databases", []))
        skills_must_csv = ", ".join(must)
        skills_nice_csv = ", ".join(nice)
        skills_all_csv = ", ".join(list(dict.fromkeys(must + nice)))
        score = confidence_score(titles, must, nice)

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
            copy_card("LinkedIn — Title (Current) • Paste into: People → Title (Current)", li_title, "copy_title_current", 10)
            # Past titles: use extended synonyms for reach
            li_title_past = ext_title
            copy_card("LinkedIn — Title (Past) • Paste into: People → Title (Past)", li_title_past, "copy_title_past", 10)
            st.markdown("</div>", unsafe_allow_html=True)
        # Companies (Current/Past)
        grid1b = st.container()
        with grid1b:
            st.markdown("<div class='grid'>", unsafe_allow_html=True)
            company_current = or_group(R.get("top_companies", []))
            company_past = or_group(R.get("top_companies", []) + R.get("adjacent", []))
            copy_card("LinkedIn — Company (Current) • Paste into: People → Company (Current)", company_current, "copy_company_current", 8)
            copy_card("LinkedIn — Company (Past) • Paste into: People → Company (Past)", company_past, "copy_company_past", 8)
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

        # ---- 🔗 Quick Actions ----
        st.markdown("### 🔗 Quick Actions")
        # Build safer preview variants for LinkedIn
        k_only, tk_lite, k_full = _preview_variants_for_linkedin(titles, must, nice, li_keywords)
        ln_base = "https://www.linkedin.com/search/results/people/?keywords="
        try:
            if hasattr(st, "link_button"):
                st.link_button("🔎 Preview: Keywords (no NOT) — safe", ln_base + quote_plus(k_only))
                st.link_button("🔎 Preview: Titles + Keywords (lite)", ln_base + quote_plus(tk_lite))
                st.link_button("🔎 Preview: Full Boolean", ln_base + quote_plus(k_full))
            else:
                st.markdown(f"[🔎 Preview: Keywords (no NOT) — safe]({ln_base + quote_plus(k_only)})  ")
                st.markdown(f"[🔎 Preview: Titles + Keywords (lite)]({ln_base + quote_plus(tk_lite)})  ")
                st.markdown(f"[🔎 Preview: Full Boolean]({ln_base + quote_plus(k_full)})")
        except Exception:
            pass
        # share link builder (unchanged)
        params = {
            "role": st.session_state.get("any_title",""),
            "cat": cat,
            "titles": "|".join([t for t in titles if t]),
            "must": ",".join(must),
            "nice": ",".join(nice),
            "not": ",".join(st.session_state.get("jd_not", []) + [t.strip() for t in (extra_not or "").split(",") if t.strip()]),
            "extras": "|".join(selected_extras),
            "inc": "1" if include_extras_core else "0",
            "loc": st.session_state.get("location","") or "",
        }
        qs = urlencode(params, doseq=False)
        share_html = f"""
        <div class='cardlite'>
          <div style='display:flex;justify-content:space-between;align-items:center;'>
            <div class='blocktitle'>Shareable link</div>
            <button class='btncopy' onclick=\"navigator.clipboard.writeText(document.getElementById('share_url').value)\">Copy</button>
          </div>
          <textarea id='share_url' class='textarea' rows='2'></textarea>
          <script>
            const qs = "{qs}";
            const base = window.location.origin + window.location.pathname;
            const url = base + "?" + qs;
            document.getElementById('share_url').value = url;
          </script>
        """
        components.html(share_html, height=170)
        # store a light preview for any sticky bar usage
        ln_light_q = quote_plus(k_only)

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
