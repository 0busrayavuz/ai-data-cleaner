import streamlit as st
from components.layout import apply_custom_style
# Lazy imports to avoid circular dependencies if any, though here it's fine
from views.analyze import show_analyze_page
from views.profile import show_profile_page

# Set page config
st.set_page_config(
    page_title="PREDATA | Minimalist AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Apply Antigravity Design System
apply_custom_style()

# --- Custom Top Navigation Bar (Ultra Minimalist) ---
st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True) # Top Spacer

# Layout: Logo (Text) | Spacer | Home | Analyze | Profile | Spacer
# We can use a simple text for the logo or an emoji
col_logo, col_space1, col_home, col_analyze, col_profile, col_space2 = st.columns([1, 3, 1, 1, 1, 3])

with col_logo:
    st.markdown('<h3 style="margin:0; font-size: 24px;">PREDATA.</h3>', unsafe_allow_html=True)

with col_home:
    if st.button("HOME", key="nav_home", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()

with col_analyze:
    if st.button("ANALiZ", key="nav_analyze", use_container_width=True):
        st.session_state.page = "Analyze"
        st.rerun()

with col_profile:
    if st.button("PROFiL", key="nav_profile", use_container_width=True):
        st.session_state.page = "Profile"
        st.rerun()

st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True) # Spacer before content

# --- Router Logic ---

if st.session_state.page == 'Home':
    # --- HERO SECTION (Minimalist Text) ---
    
    st.markdown(r"""
        <div class="hero-container">
            <h1 class="hero-title">Merhaba<br>Data Scientist.</h1>
            <p class="hero-subtitle">Experience the future of data cleaning.<br>Fast. Intelligent. Native.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Marquee (Fixed Bottom)
    st.markdown(r"""
        <div class="marquee-container">
            <div class="marquee-content">
                <span class="marquee-item">PREDATA AI ENGINE</span>
                <span class="marquee-item">SECURE DATA HANDLING</span>
                <span class="marquee-item">AUTOMATED INSIGHTS</span>
                <span class="marquee-item">INSTANT CLEANING</span>
                <span class="marquee-item">EXPORT TO CSV/EXCEL</span>
                <span class="marquee-item">PREDATA AI ENGINE</span>
                <span class="marquee-item">SECURE DATA HANDLING</span>
                <span class="marquee-item">AUTOMATED INSIGHTS</span>
                <span class="marquee-item">INSTANT CLEANING</span>
                <span class="marquee-item">EXPORT TO CSV/EXCEL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == 'Analyze':
    show_analyze_page()

elif st.session_state.page == 'Profile':
    show_profile_page()