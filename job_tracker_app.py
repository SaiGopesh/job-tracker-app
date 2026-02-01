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
import calendar
from datetime import date

def get_monthly_calendar(year, month):
    records = job_sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(columns=["date", "count"])

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["count"] = df["count"].astype(int)

    daily = df.groupby("date")["count"].sum()

    cal = calendar.Calendar().monthdatescalendar(year, month)

    calendar_data = []
    date_labels = []

    for week in cal:
        row = []
        label_row = []
        for day in week:
            label_row.append(day.day)

            if day.month != month:
                row.append(None)
            else:
                row.append(daily.get(day, 0))  # 👈 missing days = 0
        calendar_data.append(row)
        date_labels.append(label_row)

    calendar_df = pd.DataFrame(
        calendar_data,
        columns=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )

    label_df = pd.DataFrame(
        date_labels,
        columns=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )

    return calendar_df, label_df

def style_calendar(val):
    if val is None:
        return "background-color: #f0f0f0; color: #999999"  # grey
    if int(val) >= DAILY_TARGET:
        return "background-color: #b7eb8f; color: black"  # green
    else:
        return "background-color: #ffa39e; color: black"  # red
def render_calendar(calendar_df, label_df):
    display_df = calendar_df.copy()

    for col in display_df.columns:
        display_df[col] = display_df[col].astype("object")

    for i in range(display_df.shape[0]):
        for j, col in enumerate(display_df.columns):
            jobs = calendar_df.iloc[i, j]
            day = label_df.iloc[i, j]

            if jobs is None:
                display_df.iloc[i, j] = ""
            else:
                display_df.iloc[i, j] = f"{day}\n{jobs} jobs"

    return display_df




def get_job_df():
    return pd.DataFrame(job_sheet.get_all_records())

def get_tech_df():
    return pd.DataFrame(tech_sheet.get_all_records())

# Streamlit UI
st.title("📌 Daily Job & Learning Tracker")
section = st.sidebar.radio("Go to", ["Job Applications", "Tech Learning", "Logs"])

if section == "Job Applications":
    st.header("💼 Job Application Tracker")

    date = st.date_input("Date", value=datetime.today())

    platforms = st.multiselect(
        "Select Platforms",
        ["LinkedIn", "JobTeaser", "Ehub", "Other"],
        default=["LinkedIn"]
    )

    custom_platform = ""
    if "Other" in platforms:
        custom_platform = st.text_input("Enter platform name")

    with st.form("job_form"):
        entries = []

        for p in platforms:
            count = st.number_input(
                f"Jobs applied on {p}",
                min_value=0,
                step=1,
                key=f"count_{p}"
            )

            cp = custom_platform if p == "Other" else ""
            entries.append((p, cp, count))

        submitted = st.form_submit_button("Save Entry")

        if submitted:
            for p, cp, count in entries:
                append_job_log(date, p, cp, count)

            st.success("✅ Job logs updated!")
            today_total = get_today_job_count(date)
            remaining = DAILY_TARGET - today_total
            
            
            st.markdown("---")
            st.subheader("🎯 Daily Progress")
            
            st.write(f"✅ Jobs applied today: **{today_total}** / {DAILY_TARGET}")
            progress_pct = min(today_total / DAILY_TARGET, 1.0)
            st.progress(progress_pct)
            st.caption(f"{int(progress_pct * 100)}% of daily target completed")
            if remaining > 0:
                st.info(f"💪 {remaining} jobs left to reach today’s target!")
            else:
                st.success("🎉 Congratulations! You’ve reached today’s job application target!")
                streak = get_target_streak()
                if streak > 0:
                    st.success(f"🔥 Current streak: {streak} day(s) hitting your target!")
                else:
                    st.info("No active streak yet — today can be Day 1 💪")

            




elif section == "Tech Learning":
    st.header("📚 Technology Learning Tracker")

    date = st.date_input("Date", value=datetime.today())
    tech = st.text_input("Technology Name")
    progress = st.text_input("Progress")

    source = st.selectbox(
        "Source",
        ["YouTube", "Course", "Documentation", "Other"]
    )

    custom_source = ""
    if source == "Other":
        custom_source = st.text_input("Enter source name")

    with st.form("tech_form"):
        submitted = st.form_submit_button("Save Progress")

        if submitted and tech:
            append_tech_log(date, tech, progress, source, custom_source)
            st.success("✅ Tech log updated!")


elif section == "Logs":
    st.header("📊 Logs Overview")

    st.subheader("📈 Daily Job Application Trend")
    daily_df = get_daily_job_summary()

    if not daily_df.empty:
        st.line_chart(
            daily_df.set_index("date")["count"]
        )
    else:
        st.info("No job application data yet.")

    st.markdown("---")

    st.subheader("📋 Job Logs")
    st.dataframe(get_job_df())

    st.subheader("📚 Tech Learning Logs")
    st.dataframe(get_tech_df())
    summary = get_weekly_summary()

    if summary:
        total, avg, hit_days = summary

        st.subheader("📆 Weekly Summary")
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Jobs", total)
        col2.metric("Daily Average", avg)
        col3.metric("Target Hit Days", hit_days)
    weekly_df = get_weekly_report_df()
    if not weekly_df.empty:
        csv = weekly_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Weekly Report (CSV)",
            data=csv,
            file_name="weekly_job_report.csv",
            mime="text/csv"
        )
    from datetime import date

    st.markdown("---")
    st.subheader("📅 Monthly Target Calendar")

    today = date.today()

    col1, col2 = st.columns(2)
    year = col1.selectbox("Year", [today.year - 1, today.year, today.year + 1], index=1)
    month = col2.selectbox(
    "Month",
    list(range(1, 13)),
    format_func=lambda x: calendar.month_name[x],
    index=today.month - 1
    )

    calendar_df, label_df = get_monthly_calendar(year, month)
    display_df = render_calendar(calendar_df, label_df)

    st.dataframe(
    display_df.style.applymap(style_calendar),
    use_container_width=True,
    height=350
    )

    st.caption("🟢 Target achieved • 🔴 Target missed • Grey = outside month")




