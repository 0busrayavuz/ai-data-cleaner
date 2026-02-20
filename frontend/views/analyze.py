import streamlit as st
import pandas as pd
import numpy as np


# ─── Helper: compute Data Health Score ────────────────────────────────────────

def _compute_health(df: pd.DataFrame):
    """Returns (score 0-100, missing_pct, dup_pct, outlier_pct)."""
    total_cells = df.size if df.size > 0 else 1
    missing_pct = round(df.isnull().sum().sum() / total_cells * 100, 1)

    dup_pct = round(df.duplicated().sum() / max(len(df), 1) * 100, 1)

    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        zscores = ((numeric - numeric.mean()) / numeric.std(ddof=0)).abs()
        outlier_count = (zscores > 3).any(axis=1).sum()
        outlier_pct = round(outlier_count / max(len(df), 1) * 100, 1)
    else:
        outlier_pct = 0.0

    score = max(0, min(100, round(100 - missing_pct * 0.5 - dup_pct * 0.3 - outlier_pct * 0.2)))
    return score, missing_pct, dup_pct, outlier_pct


# ─── Helper: render SVG gauge ─────────────────────────────────────────────────

def _gauge_html(score: int) -> str:
    """Returns an inline SVG circular gauge for score 0-100."""
    # colour: red < 50, amber < 75, green >= 75
    if score >= 75:
        color = "#27AE60"
        label_color = "#27AE60"
    elif score >= 50:
        color = "#F39C12"
        label_color = "#F39C12"
    else:
        color = "#E74C3C"
        label_color = "#E74C3C"

    radius = 70
    circumference = 2 * 3.14159 * radius
    dash = circumference * score / 100
    gap = circumference - dash

    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; padding: 10px 0 20px 0;">
        <svg width="180" height="180" viewBox="0 0 180 180">
            <!-- Background track -->
            <circle cx="90" cy="90" r="{radius}"
                fill="none" stroke="#E8EDF2" stroke-width="14"/>
            <!-- Progress arc -->
            <circle cx="90" cy="90" r="{radius}"
                fill="none" stroke="{color}" stroke-width="14"
                stroke-linecap="round"
                stroke-dasharray="{dash:.1f} {gap:.1f}"
                transform="rotate(-90 90 90)"
                style="transition: stroke-dasharray 1s ease;"/>
            <!-- Score text -->
            <text x="90" y="85" text-anchor="middle"
                font-family="Playfair Display, serif"
                font-size="36" font-weight="700"
                fill="{label_color}">{score}</text>
            <text x="90" y="108" text-anchor="middle"
                font-family="Inter, sans-serif"
                font-size="13" fill="#7F8C8D">/100</text>
        </svg>
        <p style="margin:0; font-family:'Inter',sans-serif; font-size:13px;
                  color:#7F8C8D; letter-spacing:2px; text-transform:uppercase;
                  font-weight:600;">Health Score</p>
    </div>
    """


# ─── Helper: card wrappers ────────────────────────────────────────────────────

def _card_start(header: str) -> str:
    return f"""
    <div class="ag-card">
        <div class="ag-card-header">{header}</div>
        <div class="ag-card-body">
    """

def _card_end() -> str:
    return "</div></div>"


# ─── Main page function ───────────────────────────────────────────────────────

def show_analyze_page():

    # ── Page title ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 30px 0;">
        <p style="font-family:'Inter',sans-serif; font-size:12px; font-weight:700;
                  letter-spacing:4px; text-transform:uppercase; color:#FF8C00;
                  margin-bottom:8px;">PREDATA ENGINE</p>
        <h1 style="font-family:'Playfair Display',serif; font-size:52px;
                   font-weight:700; color:#2C3E50 !important; margin:0;
                   letter-spacing:-1px; line-height:1.1;">
            Data Intelligence Studio
        </h1>
        <p style="font-family:'Inter',sans-serif; font-size:16px; color:#7F8C8D;
                  margin-top:12px; font-weight:300;">
            Upload → Diagnose → Clean → Export
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 1. Upload card ───────────────────────────────────────────────────────
    st.markdown(_card_start("① Upload Dataset"), unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop a CSV, Excel or TXT file here",
        type=["csv", "xlsx", "txt"],
        label_visibility="visible"
    )
    st.markdown(_card_end(), unsafe_allow_html=True)

    if uploaded_file is None:
        return  # Nothing more to show until file is uploaded

    # ── Read file ────────────────────────────────────────────────────────────
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine="python")
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return

    # ── 2. Data Health Score ─────────────────────────────────────────────────
    score, missing_pct, dup_pct, outlier_pct = _compute_health(df)

    st.markdown(_card_start("② Data Health Score"), unsafe_allow_html=True)

    g_col, stats_col = st.columns([1, 2])

    with g_col:
        st.markdown(_gauge_html(score), unsafe_allow_html=True)

    with stats_col:
        st.markdown("<br>", unsafe_allow_html=True)

        def _stat(label, value, color):
            return f"""
            <div style="display:flex; align-items:center; margin-bottom:18px;">
                <div style="width:10px; height:10px; border-radius:50%;
                            background:{color}; margin-right:12px; flex-shrink:0;"></div>
                <div>
                    <p style="margin:0; font-family:'Inter',sans-serif;
                              font-size:11px; text-transform:uppercase;
                              letter-spacing:2px; color:#7F8C8D; font-weight:600;">{label}</p>
                    <p style="margin:0; font-family:'Playfair Display',serif;
                              font-size:24px; font-weight:700; color:#2C3E50;">{value}%</p>
                </div>
            </div>"""

        st.markdown(
            _stat("Missing Values", missing_pct, "#E74C3C") +
            _stat("Duplicate Rows", dup_pct, "#F39C12") +
            _stat("Outliers (Z>3)", outlier_pct, "#9B59B6"),
            unsafe_allow_html=True
        )

    st.markdown(_card_end(), unsafe_allow_html=True)

    # ── 3. Data Preview ──────────────────────────────────────────────────────
    st.markdown(_card_start("③ Data Preview"), unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-family:Inter,sans-serif; font-size:13px; color:#7F8C8D; margin-bottom:10px;">'
        f'{len(df):,} rows × {len(df.columns)} columns</p>',
        unsafe_allow_html=True
    )
    st.dataframe(df.head(10), use_container_width=True)
    st.markdown(_card_end(), unsafe_allow_html=True)

    # ── 4. Configure Cleaning ────────────────────────────────────────────────
    st.markdown(_card_start("④ Configure Cleaning"), unsafe_allow_html=True)

    col_a, divider_col, col_b = st.columns([5, 1, 5])

    with col_a:
        st.markdown("""
        <div class="ag-clean-label">
            <span class="ag-badge ag-badge-blue">A</span>
            Missing Values Strategy
        </div>
        """, unsafe_allow_html=True)
        missing_method = st.radio(
            "missing_method",
            options=["Simple Imputer (Mean / Mode)", "KNN Imputer"],
            label_visibility="collapsed"
        )

    with divider_col:
        st.markdown(
            '<div style="height:180px; width:1px; background:#E8EDF2; margin: 20px auto;"></div>',
            unsafe_allow_html=True
        )

    with col_b:
        st.markdown("""
        <div class="ag-clean-label">
            <span class="ag-badge ag-badge-purple">B</span>
            Outlier Treatment Strategy
        </div>
        """, unsafe_allow_html=True)
        outlier_method = st.radio(
            "outlier_method",
            options=["Z-Score Removal (|z| > 3)", "Isolation Forest"],
            label_visibility="collapsed"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:Inter,sans-serif; font-size:13px; color:#7F8C8D; margin-bottom:6px; font-weight:600; letter-spacing:1px; text-transform:uppercase;">Additional Options</p>', unsafe_allow_html=True)

    add_col1, add_col2 = st.columns(2)
    with add_col1:
        remove_duplicates = st.checkbox("Remove Duplicate Rows", value=True)
    with add_col2:
        normalize_text = st.checkbox("Normalize Text (lowercase + strip)")

    apply_missing = st.checkbox("Apply Missing Value Imputation", value=True)
    apply_outliers = st.checkbox("Apply Outlier Treatment", value=False)

    st.markdown(_card_end(), unsafe_allow_html=True)

    # ── 5. Start cleaning ────────────────────────────────────────────────────
    if st.button("▶  START CLEANING PROCESS", key="start_clean_btn", use_container_width=True):
        with st.spinner("Applying transformations…"):
            cleaned_df = df.copy()

            try:
                # Remove duplicates
                if remove_duplicates:
                    cleaned_df = cleaned_df.drop_duplicates()

                # Missing values
                if apply_missing:
                    numeric_cols = cleaned_df.select_dtypes(include="number").columns.tolist()
                    cat_cols = cleaned_df.select_dtypes(include="object").columns.tolist()

                    if missing_method.startswith("Simple"):
                        if numeric_cols:
                            cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(
                                cleaned_df[numeric_cols].mean()
                            )
                        for col in cat_cols:
                            if not cleaned_df[col].mode().empty:
                                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])
                    else:  # KNN
                        from sklearn.impute import KNNImputer
                        if numeric_cols:
                            imputer = KNNImputer(n_neighbors=5)
                            cleaned_df[numeric_cols] = imputer.fit_transform(cleaned_df[numeric_cols])
                        for col in cat_cols:
                            if not cleaned_df[col].mode().empty:
                                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])

                # Normalize text
                if normalize_text:
                    for col in cleaned_df.select_dtypes(include="object").columns:
                        cleaned_df[col] = cleaned_df[col].str.lower().str.strip()

                # Outliers
                if apply_outliers:
                    numeric_cols = cleaned_df.select_dtypes(include="number").columns.tolist()
                    if numeric_cols:
                        if outlier_method.startswith("Z-Score"):
                            z = (cleaned_df[numeric_cols] - cleaned_df[numeric_cols].mean()) / cleaned_df[numeric_cols].std(ddof=0)
                            cleaned_df = cleaned_df[(z.abs() <= 3).all(axis=1)]
                        else:  # Isolation Forest
                            from sklearn.ensemble import IsolationForest
                            iso = IsolationForest(contamination=0.05, random_state=42)
                            preds = iso.fit_predict(cleaned_df[numeric_cols].dropna())
                            cleaned_df = cleaned_df.iloc[preds == 1]

            except ImportError as ie:
                st.error(f"Missing library: {ie}. Run `pip install scikit-learn` in your venv.")
                return
            except Exception as e:
                st.error(f"Cleaning error: {e}")
                return

        st.toast("✅ Cleaning complete!", icon="✅")

        # ── Result card ──────────────────────────────────────────────────
        after_score, *_ = _compute_health(cleaned_df)
        delta = after_score - score

        st.markdown(_card_start("⑤ Cleaning Result"), unsafe_allow_html=True)

        r_col1, r_col2, r_col3 = st.columns(3)
        r_col1.metric("Rows Before", f"{len(df):,}")
        r_col2.metric("Rows After", f"{len(cleaned_df):,}", delta=f"{len(cleaned_df)-len(df):,}")
        r_col3.metric("Health Score", f"{after_score}/100", delta=f"+{delta}" if delta >= 0 else str(delta))

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(cleaned_df.head(10), use_container_width=True)

        st.download_button(
            label="⬇  DOWNLOAD CLEANED CSV",
            data=cleaned_df.to_csv(index=False).encode("utf-8"),
            file_name="predata_cleaned.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown(_card_end(), unsafe_allow_html=True)