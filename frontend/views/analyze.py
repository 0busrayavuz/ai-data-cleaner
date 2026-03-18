import streamlit as st
import pandas as pd
import numpy as np
import requests

API_URL = "http://localhost:8000"


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
    st.markdown(_card_start("① Upload Dataset to AI Pipeline"), unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop a CSV, Excel or TXT file here",
        type=["csv", "xlsx", "txt"],
        label_visibility="visible"
    )
    st.markdown(_card_end(), unsafe_allow_html=True)

    if uploaded_file is None:
        return

    # Store dataset_id in session state to avoid re-uploading on every render
    if "dataset_id" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
        with st.spinner("Uploading to AI Data Cleaner Backend..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                res = requests.post(f"{API_URL}/upload", files=files)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["dataset_id"] = data["dataset_id"]
                    st.session_state["last_uploaded"] = uploaded_file.name
                else:
                    st.error(f"Backend upload error: {res.text}")
                    return
            except Exception as e:
                st.error(f"Backend Server Error: {e}")
                return

    dataset_id = st.session_state["dataset_id"]

    # ── 2. Analysis ──────────────────────────────────────────────────────────
    if "analysis" not in st.session_state or st.session_state.get("analysis_id") != dataset_id:
        with st.spinner("AI Analyzing the dataset..."):
            try:
                res = requests.get(f"{API_URL}/analyze/{dataset_id}")
                if res.status_code == 200:
                    st.session_state["analysis"] = res.json()
                    st.session_state["analysis_id"] = dataset_id
                else:
                    st.error("Failed to analyze dataset.")
                    return
            except Exception as e:
                st.error(f"Backend Server Error: {e}")
                return

    analysis = st.session_state["analysis"]
    profile = analysis.get("profile", {})
    recs = analysis.get("recommendations", {"total": 0, "recommendations": []})

    missing_pct = profile.get("missing_pct", 0)
    outlier_count = recs.get("outlier_count", 0)
    row_count = profile.get("row_count", 1)
    
    outlier_pct = (outlier_count / max(row_count, 1)) * 100
    score = max(0, min(100, round(100 - missing_pct * 0.5 - outlier_pct * 0.5)))

    st.markdown(_card_start("② Data Health Score (AI Assessed)"), unsafe_allow_html=True)
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
                              font-size:24px; font-weight:700; color:#2C3E50;">{value}</p>
                </div>
            </div>"""
        st.markdown(
            _stat("Missing Values", f"{missing_pct:.1f}%", "#E74C3C") +
            _stat("Outliers Discovered", f"{outlier_count} rows", "#9B59B6"),
            unsafe_allow_html=True
        )
    st.markdown(_card_end(), unsafe_allow_html=True)

    # ── 3. AI Recommendations configuration ──────────────────────────────────
    st.markdown(_card_start("③ AI Pipeline Recommendations"), unsafe_allow_html=True)
    selections = []

    if recs["total"] == 0:
        st.info("No cleaning recommendations found. Your data looks perfect!")
    else:
        st.write("Review and select the AI operations to apply:")
        for rec in recs["recommendations"]:
            st.markdown(f"**{rec['category'].capitalize()}: {rec['column']}**")
            st.caption(rec["summary"])
            options = {opt["name"]: opt["id"] for opt in rec["options"]}
            
            selected_name = st.radio(
                f"Action for {rec['column']} ({rec['category']})",
                options=list(options.keys()),
                key=rec["id"],
                label_visibility="collapsed"
            )
            selections.append({
                "category": rec["category"],
                "column": rec["column"],
                "method": options[selected_name]
            })
            st.divider()

    st.markdown(_card_end(), unsafe_allow_html=True)

    # ── 4. Apply via Backend ─────────────────────────────────────────────────
    if st.button("▶  APPLY AI PREPROCESSING", key="start_clean_btn", use_container_width=True):
        if not selections:
            st.warning("No actions selected.")
            return

        with st.spinner("Backend AI models are processing the data..."):
            try:
                res = requests.post(f"{API_URL}/apply/{dataset_id}", json={"selections": selections})
                if res.status_code == 200:
                    result = res.json()
                    st.toast("✅ Backend Cleanup Complete!", icon="✅")
                    
                    st.markdown(_card_start("④ Process Result"), unsafe_allow_html=True)
                    st.success(f"Successfully applied {result['applied_count']} AI operations.")
                    if result['error_count'] > 0:
                        st.error(f"Failed {result['error_count']} operations.")
                    
                    st.write(f"**Missing value percentage went from {result['before_missing_pct']}% to {result['after_missing_pct']}%**")
                    
                    st.markdown("### Process Logs")
                    for log in result["logs"]:
                        if log["status"] == "ok":
                            st.write(f"✅ {log['detail']}")
                        else:
                            st.write(f"❌ {log['detail']}")
                            
                    output_path = result.get("output_path", "")
                    try:
                        import os
                        if os.path.exists(output_path):
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="⬇ DOWNLOAD ENTERPRISE CLEANED DATASET",
                                    data=f,
                                    file_name=f"predata_ai_cleaned_{uploaded_file.name}",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                    except Exception:
                        st.error("Could not load the cleaned file from the output directory.")
                        
                    st.markdown(_card_end(), unsafe_allow_html=True)
                else:
                    st.error(f"Apply Failed: {res.text}")
            except Exception as e:
                st.error(f"Backend Server Error: {e}")