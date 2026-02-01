# --- Google Sheets Setup ---
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

import pandas as pd
from datetime import datetime

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
st.success("Auth OK")

job_sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1IBiJxx_DV3-4G7A4ALSOhWXEB1SxgtAPjK0Il9bQuYs"
).sheet1


tech_sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1OL7XjAEtnxDQ9-cqHZzgms6yToVD0wZOOM6eacmW5qk/edit?usp=sharing"
).sheet1


# Helper functions
def append_job_log(date, platform, custom_platform, count):
    job_sheet.append_row([str(date), platform, custom_platform, str(count)])

def append_tech_log(date, tech, progress, source, custom_source):
    tech_sheet.append_row([str(date), tech, progress, source, custom_source])

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

        platforms = st.multiselect(
            "Select Platforms",
            ["LinkedIn", "JobTeaser", "Ehub", "Other"],
            default=["LinkedIn"]
        )

        entries = []

        for p in platforms:
            count = st.number_input(
                f"Jobs applied on {p}",
                min_value=0,
                step=1,
                key=f"count_{p}"
            )

            custom_platform = ""

            if p == "Other":
                custom_platform = st.text_input(
                    "Enter platform name",
                    key="custom_platform"
                )

            entries.append((p, custom_platform, count))

        submitted = st.form_submit_button("Save Entry")

        if submitted:
            for p, custom_p, count in entries:
                append_job_log(date, p, custom_p, count)

            st.success("✅ Job logs updated!")



elif section == "Tech Learning":
    st.header("📚 Technology Learning Tracker")

    with st.form("tech_form"):
        date = st.date_input("Date", value=datetime.today())
        tech = st.text_input("Technology Name")
        progress = st.text_input("Progress")

        source = st.selectbox(
            "Source",
            ["YouTube", "Course", "Documentation", "Other"],
            key="source_select"
        )

        custom_source = ""
        if source == "Other":
            custom_source = st.text_input(
                "Enter source name",
                key="custom_source"
            )

        submitted = st.form_submit_button("Save Progress")

        if submitted and tech:
            append_tech_log(date, tech, progress, source, custom_source)
            st.success("✅ Tech log updated!")


elif section == "Logs":
    st.header("📊 Logs Overview")
    st.subheader("Jobs")
    st.dataframe(get_job_df())
    st.subheader("Tech Learning")
    st.dataframe(get_tech_df())
