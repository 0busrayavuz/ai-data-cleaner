import streamlit as st

def apply_custom_style():
    st.markdown(r"""
        <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');

        /* 
        --------------------------------------------------
        ANTIGRAVITY 2.0 DESIGN SYSTEM
        --------------------------------------------------
        */

        /* Dynamic Mesh Background */
        .stApp {
            background-color: #FAF9F6;
            background-image: 
                radial-gradient(at 0% 0%, hsla(253,16%,7%,0.3) 0px, transparent 50%),
                radial-gradient(at 50% 0%, hsla(225,39%,30%,0.3) 0px, transparent 50%),
                radial-gradient(at 100% 0%, hsla(339,49%,30%,0.3) 0px, transparent 50%);
            background-size: 200% 200%;
            animation: meshGradient 15s ease infinite;
            font-family: 'Inter', sans-serif;
        }

        @keyframes meshGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Hide Streamlit Default Elements (CRITICAL) */
        #MainMenu {visibility: hidden; display: none !important;}
        footer {visibility: hidden; display: none !important;}
        header {visibility: hidden; display: none !important;}
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}

        /* Typography Override */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Playfair Display', serif !important;
            color: #1A1A1A !important;
        }
        
        div, p, span, label, li, a, .stMarkdown, .stText {
            font-family: 'Inter', sans-serif !important;
            color: #1A1A1A !important;
        }

        /* 
        --------------------------------------------------
        UI COMPONENTS - ADVANCED GLASSMORPHISM & TILT
        --------------------------------------------------
        */

        /* Advanced Glass Card - Antigravity 2.0 */
        .glass-card {
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.4); /* Catching light */
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
            
            /* 3D Tilt Hook */
            transform-style: preserve-3d;
            perspective: 1000px;
            transition: transform 0.1s ease; /* Fast response for mouse tilt if JS used, else smooth hover */
        }

        /* Hover Effect (CSS Fallback for Tilt) */
        .glass-card:hover {
            transform: translateY(-5px) scale(1.01);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.08);
            border-color: rgba(255, 255, 255, 0.8);
        }

        /* 
        --------------------------------------------------
        NAVIGATION BAR STYLES - MICRO-INTERACTIONS
        --------------------------------------------------
        */
        
        /* Nav Buttons */
        div[data-testid="stHorizontalBlock"] button {
            background-color: transparent !important;
            border: none !important;
            color: #2C3E50 !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            transition: all 0.3s ease !important;
            padding: 10px 20px !important;
            position: relative;
            overflow: hidden;
        }

        /* Glowing Orange Underline Animation */
        div[data-testid="stHorizontalBlock"] button::after {
            content: '';
            position: absolute;
            width: 0;
            height: 2px;
            bottom: 5px;
            left: 50%;
            background-color: #FF8C00;
            transition: all 0.3s ease;
            transform: translateX(-50%);
            box-shadow: 0 0 10px #FF8C00;
        }

        div[data-testid="stHorizontalBlock"] button:hover::after {
            width: 80%;
        }

        div[data-testid="stHorizontalBlock"] button:hover {
            color: #1A1A1A !important;
            transform: translateY(-1px);
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
        }

        /* 
        --------------------------------------------------
        PAGE TRANSITIONS
        --------------------------------------------------
        */
        
        /* Fade In Animation for Main Container */
        .block-container {
            animation: fadeInScale 0.6s cubic-bezier(0.22, 1, 0.36, 1);
        }

        @keyframes fadeInScale {
            0% { 
                opacity: 0; 
                transform: scale(0.98) translateY(20px); 
            }
            100% { 
                opacity: 1; 
                transform: scale(1) translateY(0); 
            }
        }

        /* 
        --------------------------------------------------
        HOME PAGE HERO
        --------------------------------------------------
        */
        
        .hero-container {
            text-align: left;
            padding: 80px 20px;
            max-width: 1100px;
            margin: 0 auto;
            position: relative;
            z-index: 10;
        }

        .hero-title {
            font-size: 120px !important;
            font-weight: 700;
            line-height: 0.95;
            margin: 20px 0;
            color: #1A1A1A !important; 
            letter-spacing: -3px;
            
            /* Subtle Text Gradient to Deep Blue */
            background: -webkit-linear-gradient(#1A1A1A, #2C3E50);
            -webkit-background-clip: text;
            /* -webkit-text-fill-color: transparent; Caution: can cause issues with !important color override, keeping solid for safety per prompt unless requested */
        }

        .hero-subtitle {
             font-size: 1.5rem;
             color: #2C3E50 !important;
             margin-top: 30px;
             margin-bottom: 50px;
             font-weight: 300;
             opacity: 0.9;
             max-width: 700px;
             line-height: 1.5;
        }

        /* Marquee - Fixed at Bottom */
        .marquee-container {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            overflow: hidden;
            white-space: nowrap;
            padding: 15px 0;
            background: rgba(255, 255, 255, 0.85); /* Semi-transparent */
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.5);
            display: flex;
            align-items: center;
            z-index: 9998;
        }

        .marquee-content {
            display: inline-block;
            animation: marquee 30s linear infinite;
        }
        
        .marquee-item {
            display: inline-block;
            margin-right: 80px;
            color: #2C3E50 !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        
        .marquee-item::after {
            content: "✦"; /* Elegant separator */
            display: inline-block;
            margin-left: 80px;
            color: #FF8C00;
            font-size: 1.2em;
            vertical-align: middle;
        }

        @keyframes marquee {
            0% { transform: translate(0, 0); }
            100% { transform: translate(-50%, 0); }
        }

        /* 
        --------------------------------------------------
        FIXED ELEMENTS
        --------------------------------------------------
        */

        /* Floating Robot Icon */
        .floating-robot {
            position: fixed;
            bottom: 40px;
            right: 40px;
            width: 65px;
            height: 65px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(15px);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            cursor: pointer;
            z-index: 9999;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 2px solid transparent;
        }
        
        .floating-robot:hover {
            transform: scale(1.15) rotate(5deg);
            box-shadow: 0 15px 40px rgba(255, 140, 0, 0.25);
            border-color: #FF8C00;
        }
        
        /* Thought Bubble */
        .robot-thought {
            position: absolute;
            top: -45px;
            right: 50px;
            background: white;
            padding: 8px 20px;
            border-radius: 20px 20px 0 20px;
            font-size: 0.8rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s ease;
            white-space: nowrap;
            color: #2C3E50 !important;
            font-weight: 600;
            pointer-events: none;
        }

        .floating-robot:hover .robot-thought {
            opacity: 1;
            transform: translateY(0);
        }

        /* 
        --------------------------------------------------
        ANALYZE PAGE — ANTIGRAVITY FLOATING CARDS
        --------------------------------------------------
        */

        /* White floating card */
        .ag-card {
            background: #FFFFFF;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(44, 62, 80, 0.08);
            margin-bottom: 28px;
            overflow: hidden;
            transition: box-shadow 0.3s ease, transform 0.3s ease;
        }

        .ag-card:hover {
            box-shadow: 0 16px 48px rgba(44, 62, 80, 0.13);
            transform: translateY(-3px);
        }

        /* Deep blue card header */
        .ag-card-header {
            background: #2C3E50;
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 2px !important;
            text-transform: uppercase;
            padding: 14px 28px;
        }

        /* Card body padding */
        .ag-card-body {
            padding: 28px;
        }

        /* Cleaning column header label */
        .ag-clean-label {
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 700;
            color: #2C3E50 !important;
            margin-bottom: 16px;
            letter-spacing: 0.5px;
        }

        /* Column A / B badge */
        .ag-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 26px;
            height: 26px;
            border-radius: 6px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 800;
            color: #fff;
            flex-shrink: 0;
        }

        .ag-badge-blue   { background: #2C3E50; }
        .ag-badge-purple { background: #8E44AD; }

        /* Override Streamlit radio label colours inside cards */
        .ag-card-body .stRadio label {
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            color: #2C3E50 !important;
        }

        /* Start Cleaning Button */
        div[data-testid="column"] button[kind="secondary"],
        div.stButton > button {
            background: #2C3E50 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 2px !important;
            padding: 14px !important;
            transition: background 0.3s ease, transform 0.2s ease !important;
        }

        div.stButton > button:hover {
            background: #1A252F !important;
            transform: translateY(-2px) !important;
        }

        /* Download button accent */
        div.stDownloadButton > button {
            background: linear-gradient(135deg, #27AE60, #1ABC9C) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 2px !important;
        }

        </style>
        
        <!-- Persistent Robot Icon -->
        <div class="floating-robot">
            🤖
            <div class="robot-thought">Antigravity 2.0 Active</div>
        </div>
        
        <!-- 3D Tilt Script Injection (Vanilla Tilt) -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.0/vanilla-tilt.min.js"></script>
        <script>
            // Target all glass cards for title effect
            VanillaTilt.init(document.querySelectorAll(".glass-card"), {
                max: 5,
                speed: 400,
                glare: true,
                "max-glare": 0.2,
            });
        </script>
    """, unsafe_allow_html=True)