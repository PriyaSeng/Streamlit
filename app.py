import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="Data Explorer (Streamlit Cloud)", page_icon="📊", layout="wide")
st.title("📊 Data Explorer — Cloud-friendly")
st.caption("Upload a CSV/Excel file → explore → clean → visualize → (optional) PCA → download.")

# ------------------------- Helpers & Caching -------------------------
@st.cache_data(show_spinner=False)
def load_file(file, sheet_name=None):
    suffix = (file.name.split(".")[-1]).lower()
    if suffix in ["xls", "xlsx"]:
        return pd.read_excel(file, sheet_name=sheet_name)
    return pd.read_csv(file, low_memory=False)

@st.cache_data(show_spinner=False)
def memory_mb(df: pd.DataFrame) -> float:
    return float(df.memory_usage(deep=True).sum()) / (1024**2)

@st.cache_data(show_spinner=False)
def basic_stats(df: pd.DataFrame):
    desc = df.describe(include="all", datetime_is_numeric=True).T
    return desc

@st.cache_data(show_spinner=False)
def missing_table(df: pd.DataFrame):
    n = len(df)
    miss = df.isna().sum().to_frame("missing_count")
    miss["missing_pct"] = (miss["missing_count"] / n * 100).round(2)
    miss = miss[miss["missing_count"] > 0].sort_values("missing_pct", ascending=False)
    return miss

@st.cache_data(show_spinner=False)
def corr_numeric(df: pd.DataFrame):
    num = df.select_dtypes(include=np.number)
    if num.shape[1] < 2:
        return None
    return num.corr(numeric_only=True)

# ------------------------- Sidebar: data source -------------------------
with st.sidebar:
    st.header("📥 Data")
    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xls", "xlsx"])
    sheet = st.text_input("Excel sheet name (optional)")
    st.markdown("---")
    st.header("🧼 Cleaning")
    drop_dupes = st.checkbox("Drop duplicate rows", value=True)
    impute_num = st.checkbox("Impute numeric NA with median", value=True)
    impute_cat = st.checkbox("Impute categorical NA with mode", value=True)
    st.markdown("---")
    st.header("⚙️ Options")
    sample_rows = st.slider("Sample rows for speed (0 = all)", 0, 100000, 0, step=1000)
    st.caption("Sampling is only for *display* & PCA speed. Downloads use the full cleaned data.")

if file is None:
    st.info("Upload a CSV/XLSX from the sidebar to begin. You can export a sample from Excel/Sheets or a small dataset.")
    st.stop()

# ------------------------- Load data -------------------------
try:
    df_raw = load_file(file, sheet_name=sheet if sheet else None)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

if df_raw.empty:
    st.warning("Your file loaded but appears to be empty.")
    st.stop()

st.success(f"Loaded **{file.name}** · shape: `{df_raw.shape[0]} x {df_raw.shape[1]}` · memory ~ **{memory_mb(df_raw):.2f} MB**")

# Optional sample for faster UI
df_display = df_raw.sample(n=min(sample_rows, len(df_raw)), random_state=7) if sample_rows else df_raw.copy()

# ------------------------- Cleaning (non-destructive until download) -------------------------
def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if drop_dupes:
        out = out.drop_duplicates()
    if impute_num:
        for col in out.select_dtypes(include=np.number).columns:
            out[col] = out[col].fillna(out[col].median())
    if impute_cat:
        for col in out.select_dtypes(exclude=np.number).columns:
            try:
                mode_val = out[col].mode(dropna=True).iloc[0]
                out[col] = out[col].fillna(mode_val)
            except Exception:
                pass
    return out

df_clean_full = clean(df_raw)
df_clean_display = clean(df_display)

# ------------------------- Tabs -------------------------
tab1, tab2, tab3, tab4 = st.tabs(["👀 Preview", "🔎 Quality & Stats", "📈 Visualize", "🧭 PCA"])

with tab1:
    st.subheader("Data Preview")
    st.dataframe(df_clean_display.head(500), use_container_width=True)
    st.caption(f"Showing up to 500 rows (sampled = {sample_rows>0}). Full rows: {len(df_clean_full):,}")

    # Download cleaned data
    buff = io.BytesIO()
    df_clean_full.to_csv(buff, index=False)
    st.download_button(
        "⬇️ Download cleaned CSV",
        data=buff.getvalue(),
        file_name=f"cleaned_{file.name.rsplit('.',1)[0]}.csv",
        mime="text/csv",
        use_container_width=True
    )

with tab2:
    st.subheader("Schema")
    st.write(pd.DataFrame({"column": df_clean_display.columns,
                           "dtype": df_clean_display.dtypes.astype(str).values}))
    st.markdown("---")

    st.subheader("Missingness")
    miss = missing_table(df_clean_display)
    if miss is None or miss.empty:
        st.success("No missing values in the (sampled) data.")
    else:
        st.dataframe(miss, use_container_width=True)

    st.markdown("---")
    st.subheader("Descriptive Stats")
    st.dataframe(basic_stats(df_clean_display), use_container_width=True)

    st.markdown("---")
    st.subheader("Correlation (numeric)")
    corr = corr_numeric(df_clean_display)
    if corr is None:
        st.info("Not enough numeric columns for a correlation heatmap.")
    else:
        fig = px.imshow(corr, text_auto=False, aspect="auto",
                        title="Correlation heatmap (sampled numeric columns)")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Chart Builder")
    cols = df_clean_display.columns.tolist()
    x = st.selectbox("X axis", cols, index=min(0, len(cols)-1))
    y = st.selectbox("Y axis (optional)", ["(count)"] + cols, index=0)
    color = st.selectbox("Color/group (optional)", ["(none)"] + cols, index=0)
    kind = st.selectbox("Chart type", ["bar", "line", "scatter", "box"], index=0)
    agg = st.selectbox("Aggregation (if Y = count or categorical)", ["count", "sum", "mean", "median"], index=0)

    df_plot = df_clean_display.copy()

    if y == "(count)":
        # groupby count
        group_cols = [x] + ([color] if color != "(none)" else [])
        plot_df = (
            df_plot.groupby(group_cols, dropna=False)
            .size()
            .reset_index(name="count")
            .rename(columns={"count": "value"})
        )
        y_plot = "value"
    else:
        if agg == "count":
            group_cols = [x] + ([color] if color != "(none)" else [])
            plot_df = (
                df_plot.groupby(group_cols, dropna=False)[y]
                .count()
                .reset_index(name="value")
            )
            y_plot = "value"
        else:
            group_cols = [x] + ([color] if color != "(none)" else [])
            plot_df = (
                df_plot.groupby(group_cols, dropna=False)[y]
                .agg(agg)
                .reset_index(name="value")
            )
            y_plot = "value"

    if kind == "bar":
        fig = px.bar(plot_df, x=x, y=y_plot, color=None if color == "(none)" else color)
    elif kind == "line":
        fig = px.line(plot_df, x=x, y=y_plot, color=None if color == "(none)" else color, markers=True)
    elif kind == "scatter":
        # For scatter, revert to raw columns if possible
        if y != "(count)" and color != "(none)":
            fig = px.scatter(df_plot, x=x, y=y, color=color)
        elif y != "(count)":
            fig = px.scatter(df_plot, x=x, y=y)
        else:
            st.info("Scatter needs a numeric Y; switch Y from '(count)'.")
            fig = None
    else:  # box
        fig = px.box(df_plot, x=x, y=None if y == "(count)" else y, color=None if color == "(none)" else color)

    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Principal Component Analysis (numeric columns)")
    num = df_clean_display.select_dtypes(include=np.number).dropna(axis=0)
    if num.shape[1] < 2 or num.shape[0] < 2:
        st.info("Need at least 2 numeric columns and 2 rows after NA drop for PCA.")
    else:
        scale = st.checkbox("Standardize features (recommended)", value=True)
        components = st.slider("Components to compute", 2, min(10, num.shape[1]), 2)
        if scale:
            X = StandardScaler().fit_transform(num.values)
        else:
            X = num.values
        pca = PCA(n_components=components, random_state=7)
        Xp = pca.fit_transform(X)
        exp_var = (pca.explained_variance_ratio_ * 100).round(2)

        st.write(f"Explained variance: {exp_var[:3]}% for the first components.")
        fig = px.scatter(
            x=Xp[:, 0], y=Xp[:, 1],
            labels={"x": f"PC1 ({exp_var[0]}%)", "y": f"PC2 ({exp_var[1]}%)"},
            title="PCA: PC1 vs PC2 (sampled data)"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Allow download of PCA coordinates joined back to index
        pca_df = pd.DataFrame(Xp[:, :2], columns=["PC1", "PC2"], index=num.index)
        joined = df_clean_display.join(pca_df, how="left")
        buff2 = io.BytesIO()
        joined.to_csv(buff2, index=False)
        st.download_button(
            "⬇️ Download data + PCA(PC1, PC2)",
            data=buff2.getvalue(),
            file_name="data_with_pca.csv",
            mime="text/csv",
            use_container_width=True
        )

st.markdown("---")
st.caption("Tip: For huge files, upload smaller filtered extracts to stay within Community Cloud resource limits.")
