"""Streamlit UI placeholder. Upload + JSON preview are added in later steps."""

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="Odwołania2json", layout="wide")
st.title("Odwołania2json")

try:
    status = requests.get(f"{API_URL}/health", timeout=3).json().get("status")
except requests.RequestException:
    status = "niedostępne"
st.caption(f"Status API: {status}")
