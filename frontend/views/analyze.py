import streamlit as st
import pandas as pd

def show_analyze_page():
    # Page Title
    st.markdown(r'<h1 style="text-align: center; margin-bottom: 20px;">Data Analysis</h1>', unsafe_allow_html=True)
    
    # --- Upload Section (Clean White Card) ---
    st.markdown(r"<h3>1. Upload Dataset</h3>", unsafe_allow_html=True)
    
    # File Uploader
    uploaded_file = st.file_uploader("Choose a CSV, Excel or TXT file", type=["csv", "xlsx", "txt"])
        
    if uploaded_file is not None:
        try:
            # Read Logic
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else: # TXT
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
                
            # --- Data Preview ---
            st.markdown(r'<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(r"<h3>2. Data Preview</h3>", unsafe_allow_html=True)
            st.dataframe(df.head(), use_container_width=True)
            st.markdown(r'</div>', unsafe_allow_html=True)
            
            # --- Cleaning Operations ---
            st.markdown(r'<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(r"<h3>3. Configure Cleaning</h3>", unsafe_allow_html=True)
            
            # Checkbox Grid - Minimalist
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(r"**Basic**", unsafe_allow_html=True)
                remove_duplicates = st.checkbox("Remove Duplicates")
                fill_missing = st.checkbox("Fill Missing Values")
                
            with col2:
                st.markdown(r"**Advanced**", unsafe_allow_html=True)
                remove_outliers = st.checkbox("Remove Outliers (Z-Score)")
                normalize_text = st.checkbox("Normalize Text")
            
            st.markdown(r"<br>", unsafe_allow_html=True)
            
            # Primary Action Button
            if st.button("START CLEANING PROCESS", key="start_analysis_btn", use_container_width=True):
                with st.spinner("Processing..."):
                    cleaned_df = df.copy()
                    
                    # Logic
                    if remove_duplicates:
                        cleaned_df = cleaned_df.drop_duplicates()
                    
                    if fill_missing:
                         numeric_cols = cleaned_df.select_dtypes(include=['number']).columns
                         cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(cleaned_df[numeric_cols].mean())
                         obj_cols = cleaned_df.select_dtypes(include=['object']).columns
                         for col in obj_cols:
                             if not cleaned_df[col].mode().empty:
                                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])

                    if remove_outliers:
                         numeric_cols = cleaned_df.select_dtypes(include=['number']).columns
                         for col in numeric_cols:
                             mean = cleaned_df[col].mean()
                             std = cleaned_df[col].std()
                             if std > 0:
                                 cleaned_df = cleaned_df[((cleaned_df[col] - mean) / std).abs() < 3]

                    if normalize_text:
                        obj_cols = cleaned_df.select_dtypes(include=['object']).columns
                        for col in obj_cols:
                            cleaned_df[col] = cleaned_df[col].str.lower().str.strip()

                    
                    # Success
                    st.toast("Cleaning Complete", icon="✅")
                    
                    # Result Preview
                    st.markdown(r"<h4>Result Preview</h4>", unsafe_allow_html=True)
                    st.dataframe(cleaned_df.head(), use_container_width=True)

                    # Download
                    st.download_button(
                        label="DOWNLOAD CLEANED DATA",
                        data=cleaned_df.to_csv(index=False).encode('utf-8'),
                        file_name="predata_cleaned.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            st.markdown(r'</div>', unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Error processing file: {e}")