"""
app.py  —  Invesmate Analytics Dashboard  (Streamlit)

Upload 3 Excel files → get 3 interactive dashboards:
  🎥 Online  (BCMB + INSIGNIA webinars)
  🏢 Offline (Seminar operations + attendee intelligence)
  📊 Integrated (everything combined)
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
from pathlib import Path
from data_processor import process_all
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_image(_HERE / "logo.png")

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
# LOAD TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent

def _load_template(name: str) -> str:
    """Load a dashboard HTML template, searching common Streamlit Cloud paths."""
    candidates = [
        _HERE / f'template_{name}.html',
        Path(os.getcwd()) / f'template_{name}.html',
        Path('/mount/src') / _HERE.name / f'template_{name}.html',
    ]
    # Also try to find via glob
    for p in candidates:
        if p.exists():
            return p.read_text(encoding='utf-8')
    # Last resort: walk cwd
    for p in Path(os.getcwd()).rglob(f'template_{name}.html'):
        return p.read_text(encoding='utf-8')
    return None


TEMPLATES = {}
for _name in ['online', 'offline', 'integrated']:
    _t = _load_template(_name)
    if _t:
        TEMPLATES[_name] = _t
    else:
        st.error(f"❌ template_{_name}.html not found. Make sure it is committed to your repo.")
        st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────
if 'dashboards' not in st.session_state:
    st.session_state.dashboards = None   # dict: name → html string
if 'active_dash' not in st.session_state:
    st.session_state.active_dash = 'integrated'

# ──────────────────────────────────────────────────────────────────────────────
# DATA → JS INJECTION
# ──────────────────────────────────────────────────────────────────────────────

def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def build_data_js(data: dict, mode: str) -> str:
    """Build the JS data constants string to inject into a dashboard template."""
    b   = _j(data['bcmb'])
    i   = _j(data['insg'])
    off = _j(data['offline'])
    sm  = _j(data['seminar'])
    att = _j(data['att_summary'])
    ct  = _j(data['ct_stats'])
    sr  = _j(data['sr_stats'])
    loc = _j(data['loc_stats'])

    sb = "...BCMB_DATA.map(r=>({...r,course:'BCMB'}))"
    si = "...INSG_DATA.map(r=>({...r,course:'INSIGNIA'}))"
    so = "...OFFLINE_DATA.map(r=>({...r,course:'OFFLINE'}))"

    if mode == 'online':
        return (
            "const BCMB_DATA=" + b + ";"
            + "const INSG_DATA=" + i + ";"
            + "const OFFLINE_DATA=[];"
            + "const ALL_DATA=[" + sb + "," + si + "];"
            + "const SEMINAR_DATA=[];"
            + "const ATTENDEE_SUMMARY={};"
            + "const SALES_REP_STATS={};"
            + "const COURSE_TYPE_STATS={};"
            + "const LOCATION_STATS_ATT={};"
        )

    if mode == 'offline':
        return (
            "const BCMB_DATA=[];"
            + "const INSG_DATA=[];"
            + "const OFFLINE_DATA=[];"
            + "const ALL_DATA=[];"
            + "const SEMINAR_DATA=" + sm + ";"
            + "const ATTENDEE_SUMMARY=" + att + ";"
            + "const SALES_REP_STATS=" + sr + ";"
            + "const COURSE_TYPE_STATS=" + ct + ";"
            + "const LOCATION_STATS_ATT=" + loc + ";"
        )

    # integrated — all data
    return (
        "const BCMB_DATA=" + b + ";"
        + "const INSG_DATA=" + i + ";"
        + "const OFFLINE_DATA=" + off + ";"
        + "const ALL_DATA=[" + sb + "," + si + "," + so + "];"
        + "const SEMINAR_DATA=" + sm + ";"
        + "const ATTENDEE_SUMMARY=" + att + ";"
        + "const SALES_REP_STATS=" + sr + ";"
        + "const COURSE_TYPE_STATS=" + ct + ";"
        + "const LOCATION_STATS_ATT=" + loc + ";"
    )


def inject_data(template: str, data_js: str) -> str:
    return template.replace('// @@DATA@@', data_js, 1)


def build_all_dashboards(data: dict) -> dict:
    return {
        name: inject_data(TEMPLATES[name], build_data_js(data, name))
        for name in ['online', 'offline', 'integrated']
    }


# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD / HOME PAGE
# ──────────────────────────────────────────────────────────────────────────────

def show_upload_page():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      .upload-wrap { max-width:900px; margin:60px auto; padding:0 20px; font-family:'DM Sans',sans-serif; }
      .upload-hero { text-align:center; margin-bottom:48px; }
      .upload-logo { width:72px;height:72px;background:linear-gradient(135deg,#4f8ef7,#b44fe7);
        border-radius:20px;display:inline-flex;align-items:center;justify-content:center;
        font-size:36px;margin-bottom:20px;box-shadow:0 0 40px rgba(79,142,247,.4); }
      .upload-hero h1 { font-family:'Syne',sans-serif;font-size:36px;font-weight:800;
        color:#eceef5;margin:0;letter-spacing:-1px; }
      .upload-hero p { color:#4a5068;font-size:14px;margin:10px 0 0;letter-spacing:.5px;
        text-transform:uppercase; }
      .info-box { background:rgba(79,142,247,.06);border:1px solid rgba(79,142,247,.15);
        border-radius:14px;padding:18px 22px;margin-bottom:36px;color:#8a90aa;
        font-size:13px;line-height:1.7; }
      .info-box strong { color:#eceef5; }
      .upload-cards { display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:36px; }
      .upload-card { background:#0c1018;border:1px solid rgba(255,255,255,.06);
        border-radius:14px;padding:20px; }
      .upload-card .icon { font-size:28px;margin-bottom:10px; }
      .upload-card h3 { font-family:'Syne',sans-serif;font-size:13px;font-weight:700;
        color:#eceef5;margin:0 0 6px; }
      .upload-card p { font-size:11px;color:#4a5068;margin:0;line-height:1.5; }
      .dashboards-row { display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;
        margin-bottom:30px; }
      .dash-pill { border-radius:10px;padding:12px 16px;font-size:12px;font-weight:700;
        color:#fff;text-align:center; }
      .dash-online { background:linear-gradient(135deg,rgba(79,142,247,.3),rgba(180,79,231,.2));
        border:1px solid rgba(79,142,247,.3); }
      .dash-offline { background:linear-gradient(135deg,rgba(247,111,79,.3),rgba(180,79,231,.2));
        border:1px solid rgba(247,111,79,.3); }
      .dash-integrated { background:linear-gradient(135deg,rgba(79,206,143,.2),rgba(79,142,247,.2));
        border:1px solid rgba(79,206,143,.25); }
      @media(max-width:700px){ .upload-cards,.dashboards-row{grid-template-columns:1fr;} }
    </style>
    <div class="upload-wrap">
      <div class="upload-hero">
        <div class="upload-logo"><img src="logo.png" style="width:100%;height:100%;object-fit:contain;background:transparent;">
        </div>
        <h1>Invesmate Analytics Hub</h1>
        <p>Upload your Excel files · Get 3 interactive dashboards instantly</p>
      </div>

      <div class="dashboards-row">
        <div class="dash-pill dash-online">🎥 Online Dashboard<br><small style="font-weight:400;opacity:.8">BCMB + INSIGNIA webinars</small></div>
        <div class="dash-pill dash-offline">🏢 Offline Dashboard<br><small style="font-weight:400;opacity:.8">Seminar ops + attendees</small></div>
        <div class="dash-pill dash-integrated">📊 Integrated Dashboard<br><small style="font-weight:400;opacity:.8">Everything combined</small></div>
      </div>

      <div class="info-box">
        <strong>Required files (3):</strong><br>
        🔵 <strong>Free_Class_Lead_Report.xlsx</strong> — BCMB & INSIGNIA webinar performance data (needs <code>BCMB</code> and <code>INSG</code> sheets)<br>
        🟠 <strong>Offline_Seminar_Report.xlsx</strong> — Seminar financials: revenue, expenses, attendance, SB (needs <code>Offline Report</code> sheet)<br>
        🟣 <strong>Offline_Indepth_Details.xlsx</strong> — Student enrollment, payments, sales rep data (multi-sheet by location)
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload widgets
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""<div style="background:#0c1018;border:1px solid rgba(255,255,255,.06);
            border-radius:12px;padding:14px;margin-bottom:10px">
            <span style="font-size:22px">🔵</span>
            <div style="font-family:'Syne',sans-serif;font-size:12px;font-weight:700;
              color:#eceef5;margin:6px 0 3px">Free Class Lead Report</div>
            <div style="font-size:10px;color:#4a5068">BCMB & INSIGNIA webinar data</div>
            </div>""", unsafe_allow_html=True)
        webinar_file = st.file_uploader(
            "Free Class Lead Report", type=['xlsx', 'xls'],
            key='webinar', label_visibility='collapsed')

    with col2:
        st.markdown("""<div style="background:#0c1018;border:1px solid rgba(255,255,255,.06);
            border-radius:12px;padding:14px;margin-bottom:10px">
            <span style="font-size:22px">🟠</span>
            <div style="font-family:'Syne',sans-serif;font-size:12px;font-weight:700;
              color:#eceef5;margin:6px 0 3px">Offline Seminar Report</div>
            <div style="font-size:10px;color:#4a5068">Seminar ops, revenue, expenses</div>
            </div>""", unsafe_allow_html=True)
        seminar_file = st.file_uploader(
            "Offline Seminar Report", type=['xlsx', 'xls'],
            key='seminar', label_visibility='collapsed')

    with col3:
        st.markdown("""<div style="background:#0c1018;border:1px solid rgba(255,255,255,.06);
            border-radius:12px;padding:14px;margin-bottom:10px">
            <span style="font-size:22px">🟣</span>
            <div style="font-family:'Syne',sans-serif;font-size:12px;font-weight:700;
              color:#eceef5;margin:6px 0 3px">Attendee Details</div>
            <div style="font-size:10px;color:#4a5068">Students, payments, sales reps</div>
            </div>""", unsafe_allow_html=True)
        attendee_file = st.file_uploader(
            "Attendee Details", type=['xlsx', 'xls'],
            key='attendee', label_visibility='collapsed')

    # Status + generate button
    all_uploaded = webinar_file and seminar_file and attendee_file
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if all_uploaded:
            if st.button("🚀  Generate All 3 Dashboards", use_container_width=True, type="primary"):
                with st.spinner("Parsing files and building dashboards…"):
                    try:
                        data = process_all(webinar_file, seminar_file, attendee_file)

                        if data['errors']:
                            for e in data['errors']:
                                st.warning(f"⚠️ {e}")

                        st.session_state.dashboards = build_all_dashboards(data)
                        st.session_state.active_dash = 'integrated'

                        s = data['stats']
                        st.success(
                            f"✅  Built 3 dashboards  —  "
                            f"BCMB: {s['bcmb_count']} sessions  ·  "
                            f"INSIGNIA: {s['insg_count']} sessions  ·  "
                            f"Offline: {s['seminar_count']} seminars ({s['locations']} locations)  ·  "
                            f"Students: {s['students']:,}"
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            missing = []
            if not webinar_file:  missing.append("Free Class Lead Report")
            if not seminar_file:  missing.append("Offline Seminar Report")
            if not attendee_file: missing.append("Attendee Details")
            st.markdown(f"""
            <div style="text-align:center;padding:14px;background:rgba(255,255,255,.02);
              border:1px solid rgba(255,255,255,.05);border-radius:10px;
              color:#4a5068;font-size:13px;font-family:'DM Sans',sans-serif">
              Waiting for: <strong style="color:#8a90aa">{' · '.join(missing)}</strong>
            </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD VIEWER PAGE
# ──────────────────────────────────────────────────────────────────────────────

DASH_META = {
    'online':     {'label': '🎥 Online',      'desc': 'BCMB & INSIGNIA Webinars'},
    'offline':    {'label': '🏢 Offline',     'desc': 'Seminar Ops & Attendees'},
    'integrated': {'label': '📊 Integrated',  'desc': 'Online + Offline Combined'},
}

DASH_HEIGHTS = {
    'online':     920,
    'offline':    920,
    'integrated': 920,
}


def show_dashboard_page():
    dashboards = st.session_state.dashboards
    active     = st.session_state.active_dash

    # Top control bar
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
    <style>
      .dash-bar { display:flex;align-items:center;gap:12px;padding:10px 20px;
        background:#0c1018;border-bottom:1px solid rgba(255,255,255,.06);flex-wrap:wrap; }
      .dash-logo { width:32px;height:32px;background:linear-gradient(135deg,#4f8ef7,#b44fe7);
        border-radius:9px;display:inline-flex;align-items:center;justify-content:center;
        font-size:18px;flex-shrink:0; }
      .dash-title { font-family:'Syne',sans-serif;font-size:14px;font-weight:800;
        color:#eceef5;letter-spacing:-.3px; }
    </style>
    """, unsafe_allow_html=True)

    col_logo, col_tabs, col_reset = st.columns([1, 5, 1])

    with col_logo:
        st.markdown(f"""
<div class="dash-logo">
  <img src="data:image/png;base64,{logo_base64}" 
       style="width:100%;height:100%;object-fit:contain;">
</div>
""", unsafe_allow_html=True)

    with col_tabs:
        tab_cols = st.columns(3)
        for i, (key, meta) in enumerate(DASH_META.items()):
            with tab_cols[i]:
                is_active = key == active
                if st.button(
                    f"{meta['label']}",
                    key=f"tab_{key}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.active_dash = key
                    st.rerun()

    with col_reset:
        if st.button("← New Files", use_container_width=True):
            st.session_state.dashboards = None
            st.session_state.active_dash = 'integrated'
            st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Render active dashboard
    html = dashboards[active]
    components.html(html, height=DASH_HEIGHTS[active], scrolling=True)


# ──────────────────────────────────────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.dashboards:
    show_dashboard_page()
else:
    show_upload_page()
