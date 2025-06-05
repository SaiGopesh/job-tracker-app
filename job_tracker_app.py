import streamlit as st
import pandas as pd
from datetime import datetime

# Load or initialize job log
@st.cache_data
def load_job_log():
    try:
        return pd.read_csv("job_log.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Platform", "Jobs Applied"])

# Load or initialize tech log
@st.cache_data
def load_tech_log():
    try:
        return pd.read_csv("tech_log.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Technology", "Progress", "Source"])

job_log = load_job_log()
tech_log = load_tech_log()

st.title("📌 Daily Job & Learning Tracker")

st.sidebar.header("🧭 Navigation")
section = st.sidebar.radio("Go to", ["Job Applications", "Tech Learning", "Logs"])

# --- Job Tracker Section ---
if section == "Job Applications":
    st.header("💼 Job Application Tracker")

    with st.form("job_form"):
        st.write("### Log your job applications")
        date = st.date_input("Date", value=datetime.today())
        platforms = st.multiselect("Select Platforms", ["LinkedIn", "JobTeaser", "Ehub", "Other"], default=["LinkedIn"])
        jobs = {}
        for platform in platforms:
            jobs[platform] = st.number_input(f"Jobs applied on {platform}", min_value=0, step=1)

        submitted = st.form_submit_button("Save Entry")
        if submitted:
            new_rows = []
            for platform, count in jobs.items():
                new_rows.append({"Date": date, "Platform": platform, "Jobs Applied": count})
            job_log = pd.concat([job_log, pd.DataFrame(new_rows)], ignore_index=True)
            job_log.to_csv("job_log.csv", index=False)
            st.success("✅ Job applications logged successfully!")

# --- Tech Learning Section ---
elif section == "Tech Learning":
    st.header("📚 Technology Learning Tracker")

    with st.form("tech_form"):
        st.write("### Add or update learning progress")
        date = st.date_input("Date", value=datetime.today())
        tech = st.text_input("Technology Name")
        progress = st.text_input("Progress (e.g. 30%, 'Started')")
        source = st.text_input("Learning Source (YouTube, URL, etc.)")

        submitted = st.form_submit_button("Save Progress")
        if submitted and tech:
            tech_log = pd.concat([tech_log, pd.DataFrame([{
                "Date": date,
                "Technology": tech,
                "Progress": progress,
                "Source": source
            }])], ignore_index=True)
            tech_log.to_csv("tech_log.csv", index=False)
            st.success("✅ Technology learning progress saved!")

# --- Logs View Section ---
elif section == "Logs":
    st.header("📊 Logs Overview")

    st.subheader("📌 Job Application Log")
    st.dataframe(job_log.sort_values("Date", ascending=False))

    st.subheader("📌 Technology Learning Log")
    st.dataframe(tech_log.sort_values("Date", ascending=False))
