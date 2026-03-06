import streamlit as st
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "accounts")

st.title("Clara Agent Automation Dashboard")

# ----------------------------------------------------
# Validate outputs folder
# ----------------------------------------------------

if not os.path.exists(OUTPUT_DIR):
    st.error("No pipeline outputs found. Run pipeline first.")
    st.stop()

# ----------------------------------------------------
# Filter only account folders
# ----------------------------------------------------

accounts = [
    f for f in os.listdir(OUTPUT_DIR)
    if os.path.isdir(os.path.join(OUTPUT_DIR, f)) and f.startswith("acc_")
]

if not accounts:
    st.warning("No accounts generated yet.")
    st.stop()

# ----------------------------------------------------
# Account selector
# ----------------------------------------------------

selected = st.selectbox("Select Account", accounts)

acc_path = os.path.join(OUTPUT_DIR, selected)

v1_path = os.path.join(acc_path, "v1", "memo.json")
v2_path = os.path.join(acc_path, "v2", "memo.json")

# ----------------------------------------------------
# Display v1 memo
# ----------------------------------------------------

st.subheader("Account Memo v1")

if os.path.exists(v1_path):

    with open(v1_path, "r") as f:
        v1 = json.load(f)

    st.json(v1)

else:
    st.warning("v1 memo not found")

# ----------------------------------------------------
# Display v2 memo
# ----------------------------------------------------

st.subheader("Account Memo v2")

if os.path.exists(v2_path):

    with open(v2_path, "r") as f:
        v2 = json.load(f)

    st.json(v2)

else:
    st.warning("v2 memo not generated yet")

# ----------------------------------------------------
# Diff Viewer
# ----------------------------------------------------

diff_path = os.path.join(acc_path, "diff.json")

if os.path.exists(diff_path):

    st.subheader("Differences (v1 → v2)")

    with open(diff_path) as f:
        diff = json.load(f)

    for key, value in diff.items():

        st.markdown(f"**{key}**")

        st.write("v1:", value["v1"])
        st.write("v2:", value["v2"])

# ----------------------------------------------------
# Pipeline Metrics
# ----------------------------------------------------

metrics_path = os.path.join(BASE_DIR, "outputs", "pipeline_summary.json")

if os.path.exists(metrics_path):

    st.subheader("Pipeline Metrics")

    with open(metrics_path) as f:
        metrics = json.load(f)

    st.json(metrics)