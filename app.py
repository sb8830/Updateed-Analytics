"""
app.py  —  Invesmate Analytics Dashboard  (Streamlit)
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
import base64
from pathlib import Path
from data_processor import process_all

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invesmate Analytics Dashboard",
    page_icon="logo.png",
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
# LOAD LOGO (BASE64 FIX)
# ──────────────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_image(_HERE / "logo.png")

# ──────────────────────────────────────────────────────────────────────────────
# LOAD TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
def _load_template(name: str) -> str:
    candidates = [
        _HERE / f'template_{name}.html',
        Path(os.getcwd()) / f'template_{name}.html',
        Path('/mount/src') / _HERE.name / f'template_{name}.html',
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding='utf-8')
    for p in Path(os.getcwd()).rglob(f'template_{name}.html'):
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
# DATA HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def _j(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)

def build_data_js(data: dict, mode: str) -> str:
    b = _j(data['bcmb'])
    i = _j(data['insg'])
    off = _j(data['offline'])
    sm = _j(data['seminar'])
    att = _j(data['att_summary'])
    ct = _j(data['ct_stats'])
    sr = _j(data['sr_stats'])
    loc = _j(data['loc_stats'])

    sb = "...BCMB_DATA.map(r=>({...r,course:'BCMB'}))"
    si = "...INSG_DATA.map(r=>({...r,course:'INSIGNIA'}))"
    so = "...OFFLINE_DATA.map(r=>({...r,course:'OFFLINE'}))"

    if mode == 'online':
        return f"const BCMB_DATA={b};const INSG_DATA={i};const OFFLINE_DATA=[];const ALL_DATA=[{sb},{si}];"

    if mode == 'offline':
        return f"const SEMINAR_DATA={sm};const ATTENDEE_SUMMARY={att};const SALES_REP_STATS={sr};const COURSE_TYPE_STATS={ct};const LOCATION_STATS_ATT={loc};"

    return f"const BCMB_DATA={b};const INSG_DATA={i};const OFFLINE_DATA={off};const ALL_DATA=[{sb},{si},{so}];const SEMINAR_DATA={sm};"

def inject_data(template: str, data_js: str) -> str:
    return template.replace('// @@DATA@@', data_js, 1)

def build_all_dashboards(data: dict) -> dict:
    return {
        name: inject_data(TEMPLATES[name], build_data_js(data, name))
        for name in ['online', 'offline', 'integrated']
    }

# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_upload_page():
    st.markdown(f"""
    <style>
      .upload-wrap {{ max-width:900px; margin:60px auto; text-align:center; }}
      .upload-logo img {{ width:72px;height:72px;object-fit:contain;margin-bottom:20px; }}
      .upload-title {{ font-size:36px;font-weight:800;color:#eceef5; }}
      .upload-sub {{ color:#8a90aa;margin-top:10px; }}
    </style>

    <div class="upload-wrap">
      <div class="upload-logo">
        <img src="data:image/png;base64,{logo_base64}">
      </div>
      <div class="upload-title">Invesmate Analytics Hub</div>
      <div class="upload-sub">Upload your Excel files · Get 3 dashboards instantly</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    webinar_file = col1.file_uploader("Webinar File")
    seminar_file = col2.file_uploader("Seminar File")
    attendee_file = col3.file_uploader("Attendee File")

    if webinar_file and seminar_file and attendee_file:
        if st.button("🚀 Generate Dashboards"):
            data = process_all(webinar_file, seminar_file, attendee_file)
            st.session_state.dashboards = build_all_dashboards(data)
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_dashboard_page():
    dashboards = st.session_state.dashboards
    active = st.session_state.active_dash

    # NAVBAR WITH LOGO
    st.markdown(f"""
    <style>
    .navbar {{
        display:flex;justify-content:space-between;
        align-items:center;padding:12px 24px;
        background:#0c1018;border-bottom:1px solid rgba(255,255,255,0.06);
    }}
    .nav-left {{ display:flex;align-items:center;gap:10px; }}
    .nav-logo img {{ width:36px;height:36px; }}
    .nav-title {{ color:#eceef5;font-weight:800; }}
    </style>

    <div class="navbar">
        <div class="nav-left">
            <div class="nav-logo">
                <img src="data:image/png;base64,{logo_base64}">
            </div>
            <div class="nav-title">Invesmate Analytics</div>
        </div>
        <div style="color:#8a90aa;">Dashboard Suite</div>
    </div>
    """, unsafe_allow_html=True)

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
