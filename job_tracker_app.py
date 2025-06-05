import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Load credentials JSON (must be in same folder or hosted)
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open your two sheets
job_sheet = client.open("job_log").sheet1
tech_sheet = client.open("tech_log").sheet1

# Helper functions
def append_job_log(date, platform, count):
    job_sheet.append_row([str(date), platform, str(count)])

def append_tech_log(date, tech, progress, source):
    tech_sheet.append_row([str(date), tech, progress, source])

def get_job_df():
    return pd.DataFrame(job_sheet.get_all_records())

def get_tech_df():
    return pd.DataFrame(tech_sheet.get_all_records())

# Streamlit UI
st.title("📌 Daily Job & Learning Tracker")
section = st.sidebar.radio("Go to", ["Job Applications", "Tech Learning", "Logs"])

if section == "Job Applications":
    st.header("💼 Job Application Tracker")
    with st.form("job_form"):
        date = st.date_input("Date", value=datetime.today())
        platforms = st.multiselect("Select Platforms", ["LinkedIn", "JobTeaser", "Ehub", "Other"], default=["LinkedIn"])
        jobs = {}
        for p in platforms:
            jobs[p] = st.number_input(f"Jobs applied on {p}", min_value=0, step=1)
        if st.form_submit_button("Save Entry"):
            for platform, count in jobs.items():
                append_job_log(date, platform, count)
            st.success("✅ Job logs updated!")

elif section == "Tech Learning":
    st.header("📚 Technology Learning Tracker")
    with st.form("tech_form"):
        date = st.date_input("Date", value=datetime.today())
        tech = st.text_input("Technology Name")
        progress = st.text_input("Progress")
        source = st.text_input("Source")
        if st.form_submit_button("Save Progress") and tech:
            append_tech_log(date, tech, progress, source)
            st.success("✅ Tech log updated!")

elif section == "Logs":
    st.header("📊 Logs Overview")
    st.subheader("Jobs")
    st.dataframe(get_job_df())
    st.subheader("Tech Learning")
    st.dataframe(get_tech_df())
