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
DAILY_TARGET = 20

def get_today_job_count(selected_date):
    records = job_sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        return 0

    df["date"] = pd.to_datetime(df["date"]).dt.date
    today_df = df[df["date"] == selected_date]

    return today_df["count"].astype(int).sum()
def get_daily_job_summary():
    records = job_sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["count"] = df["count"].astype(int)

    daily_summary = df.groupby("date")["count"].sum().reset_index()
    return daily_summary
from datetime import timedelta

def get_target_streak():
    records = job_sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        return 0

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["count"] = df["count"].astype(int)

    daily = (
        df.groupby("date")["count"]
        .sum()
        .reset_index()
        .sort_values("date", ascending=False)
    )

    streak = 0
    expected_date = daily.iloc[0]["date"]  # most recent date

    for _, row in daily.iterrows():
        if row["date"] != expected_date:
            break  # ❌ missed a day → streak broken

        if row["count"] >= DAILY_TARGET:
            streak += 1
            expected_date -= timedelta(days=1)
        else:
            break  # ❌ target not met → streak broken

    return streak

def get_weekly_summary():
    records = job_sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        return None

    df["date"] = pd.to_datetime(df["date"])
    df["count"] = df["count"].astype(int)

    current_week = df["date"].dt.isocalendar().week.max()
    week_df = df[df["date"].dt.isocalendar().week == current_week]

    total = week_df["count"].sum()
    avg = round(total / 7, 1)
    hit_days = week_df.groupby(df["date"].dt.date)["count"].sum()
    hit_days = (hit_days >= DAILY_TARGET).sum()

    return total, avg, hit_days
def get_weekly_report_df():
    records = job_sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["count"] = df["count"].astype(int)

    current_week = df["date"].dt.isocalendar().week.max()
    week_df = df[df["date"].dt.isocalendar().week == current_week]

    return week_df
import pandas as pd
import calendar

# Calendar Functions
# -----------------------------
def get_monthly_calendar(df, year, month):
    """Return numeric_df (job counts) and label_df (day numbers) for month"""
    # Create empty calendar
    cal = calendar.Calendar(firstweekday=6)  # Sunday = 6, adjust if needed
    month_days = cal.monthdayscalendar(year, month)
    
    numeric_df = pd.DataFrame(month_days, dtype="float")  # start as float for NaN
    label_df = pd.DataFrame(month_days, dtype="object")   # for day numbers display

    # Fill numeric_df with job counts
    for i in range(len(month_days)):
        for j in range(len(month_days[i])):
            day = month_days[i][j]
            if day == 0:
                numeric_df.iloc[i, j] = None
            else:
                # Filter logs_df for that day
                day_count = df[
                    (pd.to_datetime(df['date']).dt.year == year) &
                    (pd.to_datetime(df['date']).dt.month == month) &
                    (pd.to_datetime(df['date']).dt.day == day)
                ]['count'].sum()
                numeric_df.iloc[i, j] = day_count
    return numeric_df, label_df

def display_calendar(numeric_df, label_df):
    """Return a display DataFrame with 'day\njobs' text"""
    display_df = numeric_df.copy().astype("object")

    for i in range(display_df.shape[0]):
        for j in range(display_df.shape[1]):
            jobs = numeric_df.iloc[i, j]
            day = label_df.iloc[i, j]
            if day == 0 or pd.isna(jobs):
                display_df.iloc[i, j] = ""
            else:
                display_df.iloc[i, j] = f"{int(day)}\n{int(jobs)} jobs"
    return display_df

def style_calendar_row(row):
    styles = []
    for jobs in row:
        if jobs == "" or jobs is None:
            styles.append("background-color: #f0f0f0; color: #999999")  # outside month
        elif jobs >= DAILY_TARGET:
            styles.append("background-color: #b7eb8f; color: black")  # green
        else:
            styles.append("background-color: #ffa39e; color: black")  # red
    return styles

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("📌 Daily Job & Learning Tracker")
section = st.sidebar.radio("Go to", ["Job Applications", "Tech Learning", "Logs", "Calendar"])

# -----------------------------
# Job Applications Form
# -----------------------------
if section == "Job Applications":
    st.header("💼 Job Application Tracker")
    with st.form("job_form"):
        date_input_val = st.date_input("Date", value=datetime.today())
        platforms = st.multiselect(
            "Select Platforms",
            ["LinkedIn", "JobTeaser", "Ehub", "Other"],
            default=["LinkedIn"]
        )
        jobs = {}
        for p in platforms:
            jobs[p] = st.number_input(f"Jobs applied on {p}", min_value=0, step=1)
        if st.form_submit_button("Save Entry"):
            total_jobs = 0
            for platform, count in jobs.items():
                append_job_log(date_input_val, platform, count)
                total_jobs += count

            remaining = max(0, DAILY_TARGET - total_jobs)
            if remaining == 0:
                st.success(f"✅ Target reached! Congratulations 🎉")
            else:
                st.info(f"Remaining jobs to reach daily target: {remaining}")

# -----------------------------
# Tech Learning Form
# -----------------------------
elif section == "Tech Learning":
    st.header("📚 Technology Learning Tracker")
    with st.form("tech_form"):
        date_input_val = st.date_input("Date", value=datetime.today())
        tech = st.text_input("Technology Name")
        progress = st.text_input("Progress")
        source = st.text_input("Source")
        if st.form_submit_button("Save Progress") and tech:
            append_tech_log(date_input_val, tech, progress, source)
            st.success("✅ Tech log updated!")

# -----------------------------
# Logs Overview
# -----------------------------
elif section == "Logs":
    st.header("📊 Logs Overview")
    st.subheader("Jobs")
    st.dataframe(get_job_df())
    st.subheader("Tech Learning")
    st.dataframe(get_tech_df())

# -----------------------------
# Calendar View
# -----------------------------
elif section == "Calendar":
    st.header("📅 Monthly Job Tracker")

    logs_df = get_job_df()
    if logs_df.empty:
        st.warning("No job logs yet!")
    else:
        today = datetime.today()
        selected_year = st.selectbox("Select Year", options=[today.year, today.year-1, today.year-2], index=0)
        selected_month = st.selectbox("Select Month", options=list(range(1, 13)), index=today.month-1)

        # Step 1: Create calendar numeric + labels
        numeric_df, label_df = get_monthly_calendar(logs_df, selected_year, selected_month)

        # Step 2: Normalize numeric_df
        numeric_df = numeric_df.apply(pd.to_numeric, errors="coerce")
        numeric_df = numeric_df.fillna(0).astype(int)

        # Step 3: Build display_df (day + jobs)
        display_df = display_calendar(numeric_df, label_df)

        # Step 4: Apply styling
        styled = display_df.style.apply(style_calendar_row, axis=1)
        st.dataframe(styled, use_container_width=True)
