import streamlit as st
import streamlit.components.v1 as components
import json
import os
from pathlib import Path
from data_processor import process_all

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG (LOGO ADDED)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invesmate Analytics Dashboard",
    page_icon="logo.png",   # ✅ YOUR LOGO HERE
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #060910; }
  div[data-testid="stToolbar"] { display: none; }
  section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# LOAD TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent

def _load_template(name: str) -> str:
    candidates = [
        _HERE / f'template_{name}.html',
        Path(os.getcwd()) / f'template_{name}.html',
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding='utf-8')
    return None

TEMPLATES = {}
for _name in ['online', 'offline', 'integrated']:
    _t = _load_template(_name)
    if _t:
        TEMPLATES[_name] = _t
    else:
        st.error(f"❌ template_{_name}.html not found.")
        st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────
if 'dashboards' not in st.session_state:
    st.session_state.dashboards = None
if 'active_dash' not in st.session_state:
    st.session_state.active_dash = 'integrated'

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def _j(obj): return json.dumps(obj, ensure_ascii=False, default=str)

def build_data_js(data, mode):
    b, i, off = _j(data['bcmb']), _j(data['insg']), _j(data['offline'])
    sm, att = _j(data['seminar']), _j(data['att_summary'])
    ct, sr, loc = _j(data['ct_stats']), _j(data['sr_stats']), _j(data['loc_stats'])

    if mode == 'online':
        return f"const BCMB_DATA={b};const INSG_DATA={i};const OFFLINE_DATA=[];const ALL_DATA=[...BCMB_DATA,...INSG_DATA];"

    if mode == 'offline':
        return f"const SEMINAR_DATA={sm};const ATTENDEE_SUMMARY={att};"

    return f"const BCMB_DATA={b};const INSG_DATA={i};const OFFLINE_DATA={off};const SEMINAR_DATA={sm};"

def inject_data(template, data_js):
    return template.replace('// @@DATA@@', data_js, 1)

def build_all_dashboards(data):
    return {n: inject_data(TEMPLATES[n], build_data_js(data, n)) for n in TEMPLATES}

# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD PAGE (LOGO ADDED)
# ──────────────────────────────────────────────────────────────────────────────
def show_upload_page():
    st.markdown("""
    <style>
    .upload-wrap { max-width:900px; margin:60px auto; text-align:center; }
    .upload-logo img {
        width:70px;
        height:70px;
        object-fit:contain;
        margin-bottom:15px;
    }
    .upload-title {
        font-size:32px;
        font-weight:800;
        color:#eceef5;
    }
    .upload-sub {
        color:#8a90aa;
        margin-bottom:30px;
    }
    </style>

    <div class="upload-wrap">
        <div class="upload-logo">
            <img src="logo.png">
        </div>
        <div class="upload-title">Invesmate Analytics Hub</div>
        <div class="upload-sub">Upload your Excel files · Get dashboards instantly</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    webinar = col1.file_uploader("Webinar File")
    seminar = col2.file_uploader("Seminar File")
    attendee = col3.file_uploader("Attendee File")

    if webinar and seminar and attendee:
        if st.button("🚀 Generate Dashboards"):
            data = process_all(webinar, seminar, attendee)
            st.session_state.dashboards = build_all_dashboards(data)
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAGE (NAVBAR WITH LOGO)
# ──────────────────────────────────────────────────────────────────────────────
def show_dashboard_page():
    dashboards = st.session_state.dashboards
    active = st.session_state.active_dash

    # 🔥 NAVBAR WITH LOGO
    st.markdown("""
    <style>
    .navbar {
        display:flex;
        justify-content:space-between;
        align-items:center;
        padding:12px 24px;
        background:#0c1018;
        border-bottom:1px solid rgba(255,255,255,0.06);
        position:sticky;
        top:0;
        z-index:999;
    }
    .nav-left {
        display:flex;
        align-items:center;
        gap:12px;
    }
    .nav-logo img {
        width:36px;
        height:36px;
        object-fit:contain;
    }
    .nav-title {
        font-size:16px;
        font-weight:800;
        color:#eceef5;
    }
    </style>

    <div class="navbar">
        <div class="nav-left">
            <div class="nav-logo">
                <img src="logo.png">
            </div>
            <div class="nav-title">Invesmate Analytics</div>
        </div>
        <div style="color:#8a90aa;">Dashboard Suite</div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    col1, col2, col3 = st.columns(3)
    if col1.button("🎥 Online"): st.session_state.active_dash = 'online'
    if col2.button("🏢 Offline"): st.session_state.active_dash = 'offline'
    if col3.button("📊 Integrated"): st.session_state.active_dash = 'integrated'

    components.html(dashboards[active], height=900)

# ──────────────────────────────────────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.dashboards:
    show_dashboard_page()
else:
    show_upload_page()
