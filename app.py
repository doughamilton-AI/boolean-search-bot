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
st.info("Type a job title (try 'Staff Machine Learning Engineer'), pick a bright theme,
