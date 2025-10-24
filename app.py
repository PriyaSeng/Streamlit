import io
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Simple Business Snapshot", page_icon="📈", layout="wide")
st.title("📈 Simple Business Snapshot")
st.caption("Upload a CSV/Excel with columns like: order_date, region, product, units, revenue, cost, customer_rating, is_returned.")

# -------------------- 1) Load data --------------------
with st.sidebar:
    st.header("1) Data")
    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xls", "xlsx"])
    use_sample = st.checkbox("Use sample data (50 rows)", value=not file)

@st.cache_data(show_spinner=False)
def load_df(uploaded_file):
    if uploaded_file.name.lower().endswith((".xls", ".xlsx")):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)

@st.cache_data(show_spinner=False)
def load_sample():
    # Minimal 50-row sample similar to retail/orders
    url = "https://raw.githubusercontent.com/streamlit/example-data/refs/heads/main/sample_retail_50rows.csv"
    # If you prefer, replace with your own hosted file or upload locally
    df = pd.read_csv(url)
    return df

if use_sample:
    try:
        df = load_sample()
    except Exception:
        st.error("Could not load the hosted sample. Upload a file instead.")
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

# Basic tidy-ups
if "order_date" in df.columns:
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

# -------------------- 2) Filters --------------------
with st.sidebar:
    st.header("2) Filters")
    # Only show filters if columns exist (keeps the app resilient)
    if "region" in df.columns:
        region_vals = ["(All)"] + sorted([x for x in df["region"].dropna().unique()])
        region = st.selectbox("Region", region_vals, index=0)
    else:
        region = "(All)"

    if "product" in df.columns:
        product_vals = ["(All)"] + sorted([x for x in df["product"].dropna().unique()])
        product = st.selectbox("Product", product_vals, index=0)
    else:
        product = "(All)"

    if "order_date" in df.columns:
        min_d = pd.to_datetime(df["order_date"]).min()
        max_d = pd.to_datetime(df["order_date"]).max()
        date_range = st.date_input("Date range", value=(min_d, max_d))
    else:
        date_range = None

# Apply filters
df_f = df.copy()
if region != "(All)" and "region" in df_f.columns:
    df_f = df_f[df_f["region"] == region]
if product != "(All)" and "product" in df_f.columns:
    df_f = df_f[df_f["product"] == product]
if date_range and "order_date" in df_f.columns:
    start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_f = df_f[(df_f["order_date"] >= start_d) & (df_f["order_date"] <= end_d)]

if df_f.empty:
    st.warning("No rows after filters. Try widening your filters.")
    st.stop()

# -------------------- 3) KPI cards --------------------
# These KPIs are easy to explain and always useful.
rev = df_f["revenue"].sum() if "revenue" in df_f.columns else None
units = df_f["units"].sum() if "units" in df_f.columns else None
rating = df_f["customer_rating"].mean() if "customer_rating" in df_f.columns else None
ret_rate = df_f["is_returned"].mean() * 100 if "is_returned" in df_f.columns else None

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Total Revenue", f"${rev:,.2f}" if rev is not None else "—")
with k2:
    st.metric("Total Units", f"{int(units):,}" if units is not None else "—")
with k3:
    st.metric("Avg Rating", f"{rating:.2f}/5" if rating is not None else "—")
with k4:
    st.metric("Return Rate", f"{ret_rate:.1f}%" if ret_rate is not None else "—")

st.markdown("---")

# -------------------- 4) Two intuitive charts --------------------
c1, c2 = st.columns(2)

# Chart A: Revenue by product (or top categorical column)
with c1:
    st.subheader("Revenue by Product")
    if "product" in df_f.columns and "revenue" in df_f.columns:
        top_prod = (
            df_f.groupby("product", dropna=False)["revenue"]
            .sum()
            .reset_index()
            .sort_values("revenue", ascending=False)
            .head(10)
        )
        fig = px.bar(top_prod, x="product", y="revenue", title=None, labels={"revenue": "Revenue ($)"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need 'product' and 'revenue' columns for this chart.")

# Chart B: Daily/Monthly revenue trend
with c2:
    st.subheader("Revenue Trend")
    if "order_date" in df_f.columns and "revenue" in df_f.columns:
        # Auto rollup by day; if you prefer monthly: df_f.resample('MS', on='order_date')['revenue'].sum()
        trend = (
            df_f.dropna(subset=["order_date"])
               .groupby(df_f["order_date"].dt.date)["revenue"]
               .sum()
               .reset_index()
               .rename(columns={"order_date": "date"})
        )
        fig2 = px.line(trend, x="date", y="revenue", markers=True, labels={"revenue": "Revenue ($)", "date": "Date"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Need 'order_date' and 'revenue' columns for this chart.")

st.markdown("---")

# -------------------- 5) Top 10 table --------------------
st.subheader("Top 10 Orders by Revenue")
if "revenue" in df_f.columns:
    # Pick common identifying columns if present
    cols_show = [c for c in ["order_id", "order_date", "region", "product", "units", "revenue"] if c in df_f.columns]
    top10 = df_f.sort_values("revenue", ascending=False).head(10)[cols_show]
    st.dataframe(top10, use_container_width=True)
else:
    st.info("Need a 'revenue' column for the top-10 table.")

# -------------------- Download current view (optional) --------------------
buff = io.BytesIO()
df_f.to_csv(buff, index=False)
st.download_button(
    "⬇️ Download filtered data (CSV)",
    data=buff.getvalue(),
    file_name="filtered_data.csv",
    mime="text/csv",
    use_container_width=True
)

st.caption("Tip: keep columns simple and consistent. Minimum recommended: order_date, product, region, units, revenue.")
