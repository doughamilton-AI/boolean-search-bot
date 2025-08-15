# Ai Sourcing Assistant — Enhanced Recruiter Tool (Streamlit App)

"""
This enhanced version of the AI Sourcing Assistant will help recruiters by adding:
1. Boolean searches (LinkedIn + Google X-ray) with copy buttons.
2. Suggested keywords (must-have + nice-to-have skills).
3. Other related job titles.
4. Top companies that hire for this skillset.
5. Tips for refining searches.
"""

import streamlit as st
from typing import List, Dict

# Example data — these could later be replaced with live API calls or CSV lookups
ROLE_PRESETS: Dict[str, Dict] = {
    "Software Engineer": {
        "titles": ["Software Engineer", "Software Developer", "Full Stack Engineer", "Backend Engineer", "Frontend Engineer"],
        "must_skills": ["python", "java", "javascript", "typescript", "react", "node"],
        "nice_skills": ["go", "aws", "gcp", "azure", "docker", "kubernetes"],
        "top_companies": ["Google", "Amazon", "Meta", "Microsoft", "Netflix", "Stripe", "Airbnb"]
    },
    "Machine Learning Engineer": {
        "titles": ["Machine Learning Engineer", "ML Engineer", "AI Engineer", "Data Scientist"],
        "must_skills": ["python", "pytorch", "tensorflow", "mlops", "docker", "kubernetes"],
        "nice_skills": ["sagemaker", "feature store", "ray", "mlflow", "langchain"],
        "top_companies": ["OpenAI", "DeepMind", "Google", "Amazon AWS AI", "Meta AI", "NVIDIA"]
    },
    "Site Reliability Engineer": {
        "titles": ["Site Reliability Engineer", "SRE", "Reliability Engineer", "Platform Engineer"],
        "must_skills": ["kubernetes", "terraform", "aws", "gcp", "linux", "bash"],
        "nice_skills": ["prometheus", "grafana", "pagerduty", "incident response"],
        "top_companies": ["Google", "LinkedIn", "Dropbox", "Shopify", "Cloudflare"]
    }
}

# Helper to make OR group for boolean

def or_group(items: List[str]) -> str:
    return "(" + " OR ".join([f'"{i}"' if " " in i else i for i in items]) + ")"

# Build boolean strings

def build_booleans(titles, must, nice):
    li_title = or_group(titles)
    li_keywords = or_group(must + nice)
    google_xray = f"site:linkedin.com/in {or_group(titles)} {or_group(must + nice)}"
    return li_title, li_keywords, google_xray

# Streamlit UI
st.set_page_config(page_title="Recruiter Sourcing Assistant", page_icon="🧲", layout="wide")
st.title("🧲 Recruiter Sourcing Assistant — Enhanced")

role_choice = st.selectbox("Select a role", list(ROLE_PRESETS.keys()))
location = st.text_input("Location (optional)")

if st.button("Generate Sourcing Data"):
    preset = ROLE_PRESETS[role_choice]
    li_title, li_keywords, google_xray = build_booleans(preset["titles"], preset["must_skills"], preset["nice_skills"])

    st.subheader("🔍 Boolean Searches")
    st.markdown("**LinkedIn Title (Current)**")
    st.code(li_title)
    st.markdown("**LinkedIn Keywords**")
    st.code(li_keywords)
    st.markdown("**Google X-ray Search**")
    st.code(google_xray)

    st.subheader("💡 Suggested Keywords")
    st.write("**Must-have skills:**", ", ".join(preset["must_skills"]))
    st.write("**Nice-to-have skills:**", ", ".join(preset["nice_skills"]))

    st.subheader("📋 Other Related Titles")
    st.write(", ".join(preset["titles"]))

    st.subheader("🏢 Top Companies Hiring for This Skillset")
    st.write(", ".join(preset["top_companies"]))

    st.subheader("📌 Tips for Refining Searches")
    st.markdown("""
    - Start broad, then narrow down with specific skills or frameworks.
    - Add location filters in LinkedIn Recruiter.
    - Use NOT terms to remove unrelated industries or levels.
    - Experiment with different combinations of must-have and nice-to-have skills.
    """)
