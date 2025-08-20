import re
import streamlit as st
from typing import List

st.set_page_config(page_title="AI Sourcing Assistant", layout="wide")


# ---------------------------- Small Role Library (extensible) ----------------------------
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
    "customer support", "help desk", "desktop support", "qa tester"
]


# ---------------------------- Helpers ----------------------------
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
    if "reliab" in s or "sre" in s or "site reliability" in s:
        return "sre"
    if ("machi
