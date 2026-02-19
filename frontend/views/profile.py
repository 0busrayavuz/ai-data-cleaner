import streamlit as st
import pandas as pd
from datetime import datetime

def show_profile_page():
    # Initialize session state for login
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True) # Spacer

    if not st.session_state.authenticated:
        # --- MINIMALIST LOGIN ---
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown(r'<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(r'<h2 style="text-align: center; margin-bottom: 20px;">Welcome Back</h2>', unsafe_allow_html=True)
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("SIGN IN", use_container_width=True):
                if username and password: 
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Please enter credentials.")
            
            st.markdown(r'</div>', unsafe_allow_html=True)

    else:
        # --- PROFILE DASHBOARD ---
        
        # User Info - Clean Text
        st.markdown(f'<h1 style="text-align: center; margin-bottom: 10px;">{st.session_state.get("username", "User")}</h1>', unsafe_allow_html=True)
        st.markdown(r'<p style="text-align: center; opacity: 0.6; margin-bottom: 40px;">PREDATA PREMIUM MEMBER</p>', unsafe_allow_html=True)
        
        # Transaction History
        st.markdown(r'<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(r'<h3 style="margin-bottom: 20px;">Analysis History</h3>', unsafe_allow_html=True)
        
        # Mock Data
        data = {
            "DATE": [datetime.now().strftime("%Y-%m-%d"), "2024-02-15", "2024-02-10"],
            "FILE": ["customer_data.csv", "sales_q1.xlsx", "inventory_logs.txt"],
            "STATUS": ["COMPLETED", "COMPLETED", "ARCHIVED"],
            "RECORDS": ["15,420", "5,600", "32,000"]
        }
        df = pd.DataFrame(data)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown(r'</div>', unsafe_allow_html=True)
        
        # Logout
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
             st.markdown(r'<div style="text-align: center; margin-top: 20px;">', unsafe_allow_html=True)
             if st.button("LOG OUT", key="logout_btn"):
                 st.session_state.authenticated = False
                 st.session_state.username = None
                 st.rerun()
             st.markdown(r'</div>', unsafe_allow_html=True)