import io
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Student Success Snapshot", page_icon="🎓", layout="wide")
st.title("🎓 Student Success Snapshot")
st.caption("Upload a CSV/Excel with columns like: term_date, program, campus, course, credits, grade_points, engagement_score, retained, advising_flag, student_id.")

# -------------------- 1) Data input --------------------
with st.sidebar:
    st.header("1) Data")
    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xls", "xlsx"])
    use_sample = st.checkbox("Use sample data (80 rows)", value=not file)

@st.cache_data(show_spinner=False)
def load_df(uploaded_file):
    if uploaded_file.name.lower().endswith((".xls", ".xlsx")):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)

@st.cache_data(show_spinner=False)
def load_sample():
    # Use the sample you downloaded from ChatGPT (upload it with your app for offline use)
    # If you host it elsewhere, you can replace this with a URL read.
    return pd.read_csv("sample_student_success_80rows.csv")

if use_sample:
    try:
        df = load_sample()
    except Exception:
        st.error("Sample file not found in the app folder. Upload a file instead.")
        st.stop()
else:
    if not file:
        st.info("Upload a CSV/XLSX or tick 'Use sample data'.")
        st.stop()
    try:
        df = load_df(file)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

# Basic tidy-ups & type handling
if "term_date" in df.columns:
    df["term_date"] = pd.to_datetime(df["term_date"], errors="coerce")

# -------------------- 2) Filters --------------------
with st.sidebar:
    st.header("2) Filters")
    prog = "(All)"
    camp = "(All)"

    if "program" in df.columns:
        prog_vals = ["(All)"] + sorted([x for x in df["program"].dropna().unique()])
        prog = st.selectbox("Program", prog_vals, index=0)

    if "campus" in df.columns:
        camp_vals = ["(All)"] + sorted([x for x in df["campus"].dropna().unique()])
        camp = st.selectbox("Campus", camp_vals, index=0)

    if "term_date" in df.columns:
        min_d = pd.to_datetime(df["term_date"]).min()
        max_d = pd.to_datetime(df["term_date"]).max()
        date_range = st.date_input("Term range", value=(min_d, max_d))
    else:
        date_range = None

# Apply filters
df_f = df.copy()
if prog != "(All)" and "program" in df_f.columns:
    df_f = df_f[df_f["program"] == prog]
if camp != "(All)" and "campus" in df_f.columns:
    df_f = df_f[df_f["campus"] == camp]
if date_range and "term_date" in df_f.columns:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_f = df_f[(df_f["term_date"] >= start_d) & (df_f["term_date"] <= end_d)]

if df_f.empty:
    st.warning("No rows after filters. Try widening your filters.")
    st.stop()

# -------------------- 3) KPI cards (clear & impactful) --------------------
total_students = df_f["student_id"].nunique() if "student_id" in df_f.columns else None
avg_gpa = df_f["grade_points"].mean() if "grade_points" in df_f.columns else None
retention_rate = df_f["retained"].mean() * 100 if "retained" in df_f.columns else None
avg_eng = df_f["engagement_score"].mean() if "engagement_score" in df_f.columns else None

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Total Students", f"{int(total_students):,}" if total_students is not None else "—")
with k2:
    st.metric("Average GPA", f"{avg_gpa:.2f}" if avg_gpa is not None else "—")
with k3:
    st.metric("Retention Rate", f"{retention_rate:.1f}%" if retention_rate is not None else "—")
with k4:
    st.metric("Avg Engagement", f"{avg_eng:.1f}" if avg_eng is not None else "—")

st.markdown("---")

# -------------------- 4) Two simple charts --------------------
c1, c2 = st.columns(2)

# A) Average GPA by Program
with c1:
    st.subheader("Average GPA by Program")
    if "program" in df_f.columns and "grade_points" in df_f.columns:
        gpa_prog = (
            df_f.groupby("program", dropna=False)["grade_points"]
            .mean()
            .reset_index()
            .sort_values("grade_points", ascending=False)
        )
        fig = px.bar(gpa_prog, x="program", y="grade_points",
                     labels={"grade_points": "Average GPA", "program": "Program"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need 'program' and 'grade_points' columns.")

# B) Retention trend over time
with c2:
    st.subheader("Retention Trend")
    if "term_date" in df_f.columns and "retained" in df_f.columns:
        trend = (
            df_f.dropna(subset=["term_date"])
               .groupby(df_f["term_date"].dt.to_period("M"))["retained"]
               .mean()
               .reset_index()
        )
        trend["term"] = trend["term_date"].astype(str)
        fig2 = px.line(trend, x="term", y="retained",
                       markers=True,
                       labels={"retained":"Retention Rate", "term":"Term (Month)"},
                       range_y=[0,1])
        fig2.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Need 'term_date' and 'retained' columns.")

st.markdown("---")

# -------------------- 5) Actionable table --------------------
st.subheader("Advising Priority (Low Engagement or Not Retained)")
if {"student_id","program","campus","engagement_score","retained","advising_flag"}.issubset(df_f.columns):
    at_risk = df_f.copy()
    # Define simple rule: engagement < 55 OR not retained OR advising_flag == 'Yes'
    at_risk["priority"] = (
        (at_risk["engagement_score"].fillna(0) < 55) |
        (~at_risk["retained"].fillna(True)) |
        (at_risk["advising_flag"].fillna("No") == "Yes")
    )
    tbl = (
        at_risk[at_risk["priority"]]
        .sort_values(["engagement_score"], na_position="first")
        [["student_id","program","campus","course","grade_points","engagement_score","retained","advising_flag"]]
        .head(10)
    )
    st.dataframe(tbl, use_container_width=True)
else:
    st.info("For the advising table, include: student_id, program, campus, course, grade_points, engagement_score, retained, advising_flag.")

# -------------------- Download current view --------------------
buff = io.BytesIO()
df_f.to_csv(buff, index=False)
st.download_button(
    "⬇️ Download filtered data (CSV)",
    data=buff.getvalue(),
    file_name="student_success_filtered.csv",
    mime="text/csv",
    use_container_width=True
)

st.caption("Explain it simply: *Pick Program/Campus/Term → see total students, GPA, retention, engagement → view trends → export list for advising.*")
