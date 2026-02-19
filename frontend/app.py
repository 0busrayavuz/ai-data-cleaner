import streamlit as st
import streamlit.components.v1 as components
from components.layout import apply_custom_style
# Lazy imports to avoid circular dependencies
from views.analyze import show_analyze_page
from views.profile import show_profile_page

# Set page config
st.set_page_config(
    page_title="PREDATA | Antigravity 2.0",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Apply Antigravity 2.0 Design System
apply_custom_style()

# --- Custom Top Navigation Bar (Antigravity 2.0) ---
st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True) 

# Layout: Logo (Text) | Spacer | Home | Analyze | Profile | Spacer
col_logo, col_space1, col_home, col_analyze, col_profile, col_space2 = st.columns([1, 2.5, 1, 1, 1, 2.5])

with col_logo:
    # Animated Gradient Text Logo
    st.markdown(r"""
    <h3 style="margin:0; font-size: 24px; font-weight: 800; letter-spacing: -1px;
               background: -webkit-linear-gradient(45deg, #1A1A1A, #2C3E50);
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;">
        PREDATA.
    </h3>
    """, unsafe_allow_html=True)

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

st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True) 

# --- Router Logic with Transitions ---

if st.session_state.page == 'Home':
    # --- HERO SECTION (3D TILT ENABLED) ---
    
    # We wrap the content in a tilt-container for JS to target
    # Note: Streamlit HTML separation means we need to bundle this creatively or rely on CSS hover fallbacks
    # layout.py handles the JS injection for .glass-card class.
    
    st.markdown(r"""
        <div class="hero-container">
            <h1 class="hero-title">Merhaba<br>Data Scientist.</h1>
            <p class="hero-subtitle">Experience the weightlessness of pure data.<br>Fast. Intelligent. Zero-Gravity.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Marquee (Fixed Bottom - Glass Effect)
    st.markdown(r"""
        <div class="marquee-container">
            <div class="marquee-content">
                <span class="marquee-item">PREDATA ANTIGRAVITY ENGINE</span>
                <span class="marquee-item">SECURE DATA HANDLING</span>
                <span class="marquee-item">AUTOMATED INSIGHTS</span>
                <span class="marquee-item">INSTANT CLEANING</span>
                <span class="marquee-item">EXPORT TO CSV/EXCEL</span>
                <span class="marquee-item">PREDATA ANTIGRAVITY ENGINE</span>
                <span class="marquee-item">SECURE DATA HANDLING</span>
                <span class="marquee-item">AUTOMATED INSIGHTS</span>
                <span class="marquee-item">INSTANT CLEANING</span>
                <span class="marquee-item">EXPORT TO CSV/EXCEL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Inject Vanilla Tilt Re-init for dynamic content
    # This minimal script ensures that if the DOM updates, tilt is re-applied
    components.html(r"""
        <script>
            const tiltElements = window.parent.document.querySelectorAll('.glass-card');
            if (window.parent.VanillaTilt) {
                window.parent.VanillaTilt.init(tiltElements, {
                    max: 8,
                    speed: 400,
                    glare: true,
                    "max-glare": 0.3,
                    perspective: 1000
                });
            }
        </script>
    """, height=0, width=0)

elif st.session_state.page == 'Analyze':
    show_analyze_page()
    # Re-init Tilt for Analyze Page cards
    components.html(r"""
        <script>
            const tiltElements = window.parent.document.querySelectorAll('.glass-card');
             if (window.parent.VanillaTilt) {
                window.parent.VanillaTilt.init(tiltElements, {
                    max: 5,
                    speed: 400,
                    glare: true,
                    "max-glare": 0.2
                });
            }
        </script>
    """, height=0, width=0)

elif st.session_state.page == 'Profile':
    show_profile_page()
    # Re-init Tilt for Profile Page cards
    components.html(r"""
        <script>
            const tiltElements = window.parent.document.querySelectorAll('.glass-card');
             if (window.parent.VanillaTilt) {
                window.parent.VanillaTilt.init(tiltElements, {
                    max: 5,
                    speed: 400,
                    glare: true,
                    "max-glare": 0.2
                });
            }
        </script>
    """, height=0, width=0)