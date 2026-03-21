"""
app.py  —  Invesmate Analytics Dashboard  (Streamlit)
Features: Logo navbar, Login system, Admin panel, 3 dashboards
"""

import streamlit as st
import streamlit.components.v1 as components
import json, os, base64, hashlib
from pathlib import Path
from data_processor import process_all

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invesmate Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  #MainMenu,footer,header{visibility:hidden}
  .block-container{padding:0!important;max-width:100%!important}
  .stApp{background:#060910}
  div[data-testid="stToolbar"]{display:none}
  section[data-testid="stSidebar"]{display:none}
  div[data-testid="stDecoration"]{display:none}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# LOGO
# ──────────────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent

def _get_logo_b64() -> str:
    for p in [_HERE / 'logo.png', Path(os.getcwd()) / 'logo.png']:
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode()
    # Walk cwd
    for p in Path(os.getcwd()).rglob('logo.png'):
        return base64.b64encode(p.read_bytes()).decode()
    return ""

LOGO_B64 = _get_logo_b64()
LOGO_SRC  = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else ""
LOGO_HTML = (
    f'<img src="{LOGO_SRC}" style="width:38px;height:38px;border-radius:50%;'
    f'object-fit:cover;border:2px solid rgba(79,206,143,.4);flex-shrink:0">'
    if LOGO_SRC else
    '<div style="width:38px;height:38px;background:linear-gradient(135deg,#1a6ab5,#4fce8f);'
    'border-radius:50%;display:flex;align-items:center;justify-content:center;'
    'font-size:20px;font-weight:900;color:#fff;flex-shrink:0">i</div>'
)

# ──────────────────────────────────────────────────────────────────────────────
# AUTH CONFIG
# ──────────────────────────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

USERS = {
    "admin":   {"hash": _hash("invesmate@2024"), "role": "admin",  "name": "Admin"},
    "analyst": {"hash": _hash("analyst@123"),    "role": "viewer", "name": "Analyst"},
    "manager": {"hash": _hash("manager@123"),    "role": "viewer", "name": "Manager"},
}

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────
for _k, _v in [('logged_in',False),('username',''),('role',''),('user_name',''),
               ('page','home'),('dashboards',None),('active_dash','integrated')]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

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
        st.error(f"❌ template_{_name}.html not found. Commit it to your repo.")
        st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# DATA INJECTION
# ──────────────────────────────────────────────────────────────────────────────
def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)

def build_data_js(data: dict, mode: str) -> str:
    b,i   = _j(data['bcmb']),  _j(data['insg'])
    off   = _j(data['offline']); sm = _j(data['seminar'])
    att   = _j(data['att_summary']); ct = _j(data['ct_stats'])
    sr,loc= _j(data['sr_stats']), _j(data['loc_stats'])
    sb = "...BCMB_DATA.map(r=>({...r,course:'BCMB'}))"
    si = "...INSG_DATA.map(r=>({...r,course:'INSIGNIA'}))"
    so = "...OFFLINE_DATA.map(r=>({...r,course:'OFFLINE'}))"
    if mode == 'online':
        return ("const BCMB_DATA="+b+";const INSG_DATA="+i+";const OFFLINE_DATA=[];"
                +"const ALL_DATA=["+sb+","+si+"];"
                +"const SEMINAR_DATA=[];const ATTENDEE_SUMMARY={};const SALES_REP_STATS={};"
                +"const COURSE_TYPE_STATS={};const LOCATION_STATS_ATT={};")
    if mode == 'offline':
        return ("const BCMB_DATA=[];const INSG_DATA=[];const OFFLINE_DATA=[];const ALL_DATA=[];"
                +"const SEMINAR_DATA="+sm+";const ATTENDEE_SUMMARY="+att+";"
                +"const SALES_REP_STATS="+sr+";const COURSE_TYPE_STATS="+ct+";"
                +"const LOCATION_STATS_ATT="+loc+";")
    return ("const BCMB_DATA="+b+";const INSG_DATA="+i+";const OFFLINE_DATA="+off+";"
            +"const ALL_DATA=["+sb+","+si+","+so+"];"
            +"const SEMINAR_DATA="+sm+";const ATTENDEE_SUMMARY="+att+";"
            +"const SALES_REP_STATS="+sr+";const COURSE_TYPE_STATS="+ct+";"
            +"const LOCATION_STATS_ATT="+loc+";")

def inject_data(tmpl, js): return tmpl.replace('// @@DATA@@', js, 1)
def build_all_dashboards(data):
    return {n: inject_data(TEMPLATES[n], build_data_js(data, n))
            for n in ['online','offline','integrated']}

# ──────────────────────────────────────────────────────────────────────────────
# SHARED NAVBAR
# ──────────────────────────────────────────────────────────────────────────────
def render_navbar(active_page: str = 'home'):
    is_admin  = st.session_state.role == 'admin'
    user_name = st.session_state.user_name

    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
.im-nav{{background:linear-gradient(180deg,#0c1118 0%,#080b12 100%);
  border-bottom:1px solid rgba(255,255,255,.07);padding:0 28px;height:62px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:9999;backdrop-filter:blur(12px);}}
.im-logo-wrap{{display:flex;align-items:center;gap:11px;text-decoration:none;cursor:pointer}}
.im-brand{{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;
  color:#eceef5;letter-spacing:-.4px;line-height:1.1}}
.im-brand-sub{{font-size:9px;color:#4a5068;text-transform:uppercase;letter-spacing:1px}}
.im-user-pill{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  border-radius:20px;padding:4px 12px 4px 8px;display:flex;align-items:center;gap:7px;
  font-size:12px;color:#8a90aa}}
.im-user-dot{{width:7px;height:7px;background:#4fce8f;border-radius:50%;
  animation:udot 2s infinite;flex-shrink:0}}
@keyframes udot{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.im-role{{background:rgba(79,142,247,.12);border:1px solid rgba(79,142,247,.2);
  border-radius:8px;padding:2px 8px;font-size:9px;font-weight:700;
  color:#4f8ef7;text-transform:uppercase;letter-spacing:.5px}}
.im-role.adm{{background:rgba(247,201,72,.1);border-color:rgba(247,201,72,.2);color:#f7c948}}
</style>
<div class="im-nav">
  <div class="im-logo-wrap">
    {LOGO_HTML}
    <div>
      <div class="im-brand">Invesmate</div>
      <div class="im-brand-sub">Analytics Hub</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:10px">
    <div class="im-user-pill">
      <div class="im-user-dot"></div>
      <span>{user_name}</span>
    </div>
    <div class="im-role {'adm' if is_admin else ''}">{'Admin' if is_admin else 'Viewer'}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Navigation row
    nav_cols = st.columns([2, 1, 1, 1, 1, 2])
    with nav_cols[1]:
        if st.button("🏠 Home", key="nb_home", use_container_width=True,
                     type="primary" if active_page=='home' else "secondary"):
            st.session_state.page = 'home'; st.rerun()
    with nav_cols[2]:
        if st.button("📊 Dashboard", key="nb_dash", use_container_width=True,
                     type="primary" if active_page=='dashboard' else "secondary"):
            st.session_state.page = 'dashboard'; st.rerun()
    if is_admin:
        with nav_cols[3]:
            if st.button("⚙️ Admin", key="nb_admin", use_container_width=True,
                         type="primary" if active_page=='admin' else "secondary"):
                st.session_state.page = 'admin'; st.rerun()
    with nav_cols[4]:
        if st.button("🚪 Logout", key="nb_logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_login():
    logo_tag = (f'<img src="{LOGO_SRC}" style="width:80px;height:80px;border-radius:50%;'
                f'object-fit:cover;border:3px solid rgba(79,206,143,.4);'
                f'box-shadow:0 0 32px rgba(79,206,143,.25)">'
                if LOGO_SRC else
                '<div style="width:80px;height:80px;background:linear-gradient(135deg,#1a6ab5,#4fce8f);'
                'border-radius:50%;display:inline-flex;align-items:center;justify-content:center;'
                'font-size:36px;font-weight:900;color:#fff;box-shadow:0 0 32px rgba(79,206,143,.25)">i</div>')

    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
body,.stApp{{background:#060910}}
.login-shell{{min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:radial-gradient(ellipse at 25% 25%,rgba(79,142,247,.1) 0%,transparent 55%),
             radial-gradient(ellipse at 75% 75%,rgba(79,206,143,.07) 0%,transparent 55%),#060910;
  padding:40px 20px}}
.login-card{{background:linear-gradient(145deg,#0c1018,#090d14);
  border:1px solid rgba(255,255,255,.08);border-radius:22px;
  padding:44px 48px;width:100%;max-width:420px;
  box-shadow:0 32px 100px rgba(0,0,0,.7)}}
.lc-logo{{text-align:center;margin-bottom:24px}}
.lc-title{{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;
  color:#eceef5;text-align:center;margin:0 0 4px;letter-spacing:-.6px}}
.lc-sub{{font-size:11px;color:#4a5068;text-align:center;margin-bottom:32px;
  text-transform:uppercase;letter-spacing:.9px}}
.demo-box{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);
  border-radius:10px;padding:14px 16px;margin-top:20px}}
.demo-title{{font-size:10px;color:#4a5068;font-weight:700;text-transform:uppercase;
  letter-spacing:.6px;margin-bottom:8px}}
.demo-cred{{font-size:11px;color:#8a90aa;line-height:1.9}}
</style>
<div class="login-shell">
  <div class="login-card">
    <div class="lc-logo">{logo_tag}</div>
    <div class="lc-title">Invesmate Analytics</div>
    <div class="lc-sub">Sign in to continue</div>
  </div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<div style='margin-top:-340px'>", unsafe_allow_html=True)
        username = st.text_input("", placeholder="👤  Username", key="lu")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        password = st.text_input("", placeholder="🔑  Password", type="password", key="lp")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if st.button("Sign In  →", use_container_width=True, type="primary", key="lbtn"):
            user = USERS.get((username or '').strip().lower())
            if user and user['hash'] == _hash(password or ''):
                st.session_state.logged_in = True
                st.session_state.username  = username.strip().lower()
                st.session_state.role      = user['role']
                st.session_state.user_name = user['name']
                st.session_state.page      = 'home'
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Try again.")
        st.markdown("""
<div class="demo-box">
  <div class="demo-title">Demo credentials</div>
  <div class="demo-cred">
    👑 <strong style="color:#f7c948">admin</strong> / invesmate@2024<br>
    👤 <strong style="color:#4f8ef7">analyst</strong> / analyst@123<br>
    👤 <strong style="color:#4f8ef7">manager</strong> / manager@123
  </div>
</div>
""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HOME PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_home():
    render_navbar('home')

    logo_hero = (f'<img src="{LOGO_SRC}" style="width:96px;height:96px;border-radius:50%;'
                 f'object-fit:cover;border:3px solid rgba(79,206,143,.4);'
                 f'box-shadow:0 0 48px rgba(79,206,143,.22)">'
                 if LOGO_SRC else
                 '<div style="width:96px;height:96px;background:linear-gradient(135deg,#1a6ab5,#4fce8f);'
                 'border-radius:50%;display:inline-flex;align-items:center;justify-content:center;'
                 'font-size:44px;font-weight:900;color:#fff;box-shadow:0 0 48px rgba(79,206,143,.22)">i</div>')

    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
.home-hero{{text-align:center;padding:52px 20px 36px}}
.hero-h1{{font-family:'Syne',sans-serif;font-size:40px;font-weight:800;
  color:#eceef5;margin:16px 0 8px;letter-spacing:-1.2px}}
.hero-sub{{color:#4a5068;font-size:13px;text-transform:uppercase;letter-spacing:.8px}}
.dp-row{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;
  max-width:800px;margin:32px auto 0}}
.dp{{border-radius:12px;padding:14px 18px;font-size:12px;font-weight:700;
  color:#fff;text-align:center;border:1px solid}}
.dp-o{{background:linear-gradient(135deg,rgba(79,142,247,.2),rgba(180,79,231,.1));border-color:rgba(79,142,247,.3)}}
.dp-f{{background:linear-gradient(135deg,rgba(247,111,79,.2),rgba(180,79,231,.1));border-color:rgba(247,111,79,.3)}}
.dp-i{{background:linear-gradient(135deg,rgba(79,206,143,.15),rgba(79,142,247,.1));border-color:rgba(79,206,143,.25)}}
.infobox{{background:rgba(79,142,247,.05);border:1px solid rgba(79,142,247,.12);
  border-radius:14px;padding:18px 22px;margin:28px auto;max-width:800px;
  color:#8a90aa;font-size:13px;line-height:1.8}}
.infobox strong{{color:#eceef5}}
.up-wrap{{max-width:900px;margin:0 auto;padding:0 20px 60px}}
.up-card{{background:#0c1018;border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:14px;margin-bottom:10px}}
@media(max-width:700px){{.dp-row{{grid-template-columns:1fr}}}}
</style>
<div class="home-hero">
  {logo_hero}
  <div class="hero-h1">Invesmate Analytics Hub</div>
  <div class="hero-sub">Upload your Excel files · Generate 3 interactive dashboards instantly</div>
</div>
<div class="dp-row">
  <div class="dp dp-o">🎥 Online Dashboard<br><small style="font-weight:400;opacity:.8">BCMB + INSIGNIA webinars</small></div>
  <div class="dp dp-f">🏢 Offline Dashboard<br><small style="font-weight:400;opacity:.8">Seminar ops + attendees</small></div>
  <div class="dp dp-i">📊 Integrated Dashboard<br><small style="font-weight:400;opacity:.8">Everything combined</small></div>
</div>
<div class="infobox">
  <strong>Required files (3):</strong><br>
  🔵 <strong>Free_Class_Lead_Report.xlsx</strong> — BCMB & INSIGNIA webinar data (<code>BCMB</code> + <code>INSG</code> sheets)<br>
  🟠 <strong>Offline_Seminar_Report.xlsx</strong> — Seminar financials: revenue, expenses, attendance, SB (<code>Offline Report</code> sheet)<br>
  🟣 <strong>Offline_Indepth_Details.xlsx</strong> — Student enrollment, payments, sales rep data (multi-sheet by location)
</div>
""", unsafe_allow_html=True)

    with st.container():
        c1, c2, c3 = st.columns(3)
        for col, emoji, label, desc, key in [
            (c1,"🔵","Free Class Lead Report","BCMB & INSIGNIA webinar performance","wf"),
            (c2,"🟠","Offline Seminar Report","Revenue, expenses, attendance","sf"),
            (c3,"🟣","Attendee Details","Students, payments, sales reps","af"),
        ]:
            with col:
                st.markdown(f'<div class="up-card"><span style="font-size:22px">{emoji}</span>'
                            f'<div style="font-family:Syne,sans-serif;font-size:12px;font-weight:700;'
                            f'color:#eceef5;margin:6px 0 3px">{label}</div>'
                            f'<div style="font-size:10px;color:#4a5068">{desc}</div></div>',
                            unsafe_allow_html=True)
        wf = c1.file_uploader("wf",  type=['xlsx','xls'], key='wf', label_visibility='collapsed')
        sf = c2.file_uploader("sf",  type=['xlsx','xls'], key='sf', label_visibility='collapsed')
        af = c3.file_uploader("af",  type=['xlsx','xls'], key='af', label_visibility='collapsed')

        st.markdown("<br>", unsafe_allow_html=True)
        _, cb, _ = st.columns([1,2,1])
        with cb:
            if wf and sf and af:
                if st.button("🚀  Generate All 3 Dashboards", use_container_width=True, type="primary"):
                    with st.spinner("Parsing files and building dashboards…"):
                        try:
                            data = process_all(wf, sf, af)
                            if data['errors']:
                                for e in data['errors']: st.warning(f"⚠️ {e}")
                            st.session_state.dashboards  = build_all_dashboards(data)
                            st.session_state.active_dash = 'integrated'
                            s = data['stats']
                            st.success(f"✅ Done — BCMB:{s['bcmb_count']} · INSIGNIA:{s['insg_count']} · Offline:{s['seminar_count']} · Students:{s['students']:,}")
                            st.session_state.page = 'dashboard'
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")
                            import traceback; st.code(traceback.format_exc())
            else:
                missing = [n for n,f in [("Webinar",wf),("Seminar",sf),("Attendee",af)] if not f]
                st.markdown(f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,.02);'
                            f'border:1px solid rgba(255,255,255,.05);border-radius:10px;color:#4a5068;font-size:13px">'
                            f'Waiting for: <strong style="color:#8a90aa">{" · ".join(missing)}</strong></div>',
                            unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAGE
# ──────────────────────────────────────────────────────────────────────────────
DASH_META = {
    'online':     '🎥 Online',
    'offline':    '🏢 Offline',
    'integrated': '📊 Integrated',
}

def show_dashboard():
    render_navbar('dashboard')

    if not st.session_state.dashboards:
        st.markdown("<div style='padding:40px;text-align:center;color:#4a5068'>No dashboards yet. Upload files on the Home page.</div>", unsafe_allow_html=True)
        _, cb, _ = st.columns([1,2,1])
        with cb:
            if st.button("← Go Home", use_container_width=True):
                st.session_state.page = 'home'; st.rerun()
        return

    active = st.session_state.active_dash

    # Dashboard tab selector bar
    st.markdown("""<style>
.dash-bar{background:#0a0e16;border-bottom:1px solid rgba(255,255,255,.06);
  padding:8px 24px;display:flex;align-items:center;gap:8px}
.dash-bar-label{font-size:10px;color:#4a5068;font-weight:700;text-transform:uppercase;
  letter-spacing:.7px;margin-right:4px;white-space:nowrap}
</style>
<div class="dash-bar">
  <span class="dash-bar-label">View:</span>
</div>""", unsafe_allow_html=True)

    tc = st.columns([1,1,1,4,1])
    for idx, (key, label) in enumerate(DASH_META.items()):
        with tc[idx]:
            if st.button(label, key=f"dt_{key}", use_container_width=True,
                         type="primary" if key==active else "secondary"):
                st.session_state.active_dash = key; st.rerun()
    with tc[4]:
        if st.button("← New Files", use_container_width=True):
            st.session_state.dashboards  = None
            st.session_state.active_dash = 'integrated'
            st.session_state.page        = 'home'
            st.rerun()

    components.html(st.session_state.dashboards[active], height=920, scrolling=True)

# ──────────────────────────────────────────────────────────────────────────────
# ADMIN PANEL
# ──────────────────────────────────────────────────────────────────────────────
def show_admin():
    if st.session_state.role != 'admin':
        st.error("⛔ Access denied — Admins only.")
        return

    render_navbar('admin')

    logo_sm = (f'<img src="{LOGO_SRC}" style="width:44px;height:44px;border-radius:50%;'
               f'object-fit:cover;border:2px solid rgba(247,201,72,.4)">'
               if LOGO_SRC else
               '<div style="width:44px;height:44px;background:linear-gradient(135deg,#1a6ab5,#4fce8f);'
               'border-radius:50%;display:flex;align-items:center;justify-content:center;'
               'font-size:22px;font-weight:900;color:#fff">i</div>')

    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
.adm-wrap{{max-width:1000px;margin:0 auto;padding:30px 24px 60px}}
.adm-hdr{{display:flex;align-items:center;gap:14px;margin-bottom:28px}}
.adm-title{{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#eceef5}}
.adm-sub{{font-size:11px;color:#4a5068;margin-top:2px}}
.adm-sec{{background:#0c1018;border:1px solid rgba(255,255,255,.07);
  border-radius:14px;padding:22px 24px;margin-bottom:18px}}
.adm-sec-title{{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
  color:#f7c948;margin-bottom:16px;text-transform:uppercase;letter-spacing:.8px;
  display:flex;align-items:center;gap:7px}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}}
.stat-card{{background:#111520;border:1px solid rgba(255,255,255,.06);border-radius:12px;
  padding:16px 18px;position:relative;overflow:hidden}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--c,#4f8ef7)}}
.stat-v{{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#eceef5;line-height:1}}
.stat-l{{font-size:10px;color:#4a5068;text-transform:uppercase;letter-spacing:.6px;margin-top:6px}}
.user-row{{display:flex;align-items:center;justify-content:space-between;
  padding:11px 0;border-bottom:1px solid rgba(255,255,255,.04)}}
.user-row:last-child{{border-bottom:none}}
.uname{{font-size:13px;font-weight:600;color:#eceef5}}
.umeta{{font-size:11px;color:#4a5068;margin-top:1px}}
.badg-a{{background:rgba(247,201,72,.1);border:1px solid rgba(247,201,72,.2);
  border-radius:8px;padding:2px 8px;font-size:10px;font-weight:700;color:#f7c948}}
.badg-v{{background:rgba(79,142,247,.1);border:1px solid rgba(79,142,247,.2);
  border-radius:8px;padding:2px 8px;font-size:10px;font-weight:700;color:#4f8ef7}}
</style>
<div class="adm-wrap">
  <div class="adm-hdr">
    {logo_sm}
    <div>
      <div class="adm-title">Admin Panel</div>
      <div class="adm-sub">Manage users, credentials and system settings</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="adm-wrap">', unsafe_allow_html=True)

    # System stats
    st.markdown("""<div class="adm-sec">
  <div class="adm-sec-title">📊 System Overview</div>
  <div class="stat-grid">
    <div class="stat-card" style="--c:#4f8ef7"><div class="stat-v">3</div><div class="stat-l">Total Users</div></div>
    <div class="stat-card" style="--c:#f7c948"><div class="stat-v">1</div><div class="stat-l">Admin Accounts</div></div>
    <div class="stat-card" style="--c:#4fce8f"><div class="stat-v">3</div><div class="stat-l">Dashboards</div></div>
    <div class="stat-card" style="--c:#b44fe7"><div class="stat-v">8</div><div class="stat-l">Dashboard Tabs</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    # Users list
    st.markdown('<div class="adm-sec"><div class="adm-sec-title">👥 User Accounts</div>', unsafe_allow_html=True)
    for uname, ud in USERS.items():
        badge = '<span class="badg-a">Admin</span>' if ud['role']=='admin' else '<span class="badg-v">Viewer</span>'
        st.markdown(f"""<div class="user-row">
  <div><div class="uname">{ud['name']} <span style="color:#4a5068;font-weight:400">@{uname}</span></div>
       <div class="umeta">Role: {ud['role']}</div></div>
  <div>{badge}</div>
</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Add user
    st.markdown('<div class="adm-sec"><div class="adm-sec-title">➕ Add New User</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    nu = c1.text_input("Username",    key="nu", placeholder="username")
    nn = c2.text_input("Display Name",key="nn", placeholder="Full Name")
    np_= c3.text_input("Password",    key="np", placeholder="password", type="password")
    nr = c4.selectbox("Role",["viewer","admin"], key="nr")
    if st.button("➕ Add User", key="au_btn", type="primary"):
        if nu and nn and np_:
            if nu.lower() in USERS:
                st.warning(f"⚠️ '{nu}' already exists.")
            else:
                USERS[nu.lower()] = {"hash":_hash(np_),"role":nr,"name":nn}
                st.success(f"✅ User '{nu}' added as {nr}. (Add to USERS dict in app.py to persist.)")
        else:
            st.warning("Fill all fields.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Change password
    st.markdown('<div class="adm-sec"><div class="adm-sec-title">🔑 Change Password</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    cpu = c1.selectbox("User", list(USERS.keys()), key="cpu")
    cpn = c2.text_input("New Password",     key="cpn", type="password")
    cpc = c3.text_input("Confirm Password", key="cpc", type="password")
    if st.button("🔑 Update", key="cp_btn"):
        if cpn and cpn==cpc:
            USERS[cpu]['hash'] = _hash(cpn)
            st.success(f"✅ Password updated for {cpu}")
        elif cpn != cpc:
            st.error("Passwords don't match.")
        else:
            st.warning("Enter a new password.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Credentials reference
    st.markdown("""<div class="adm-sec">
  <div class="adm-sec-title">📋 Credentials Reference</div>
  <div style="background:#060910;border:1px solid rgba(255,255,255,.06);border-radius:10px;
    padding:16px;font-family:monospace;font-size:12px;color:#4fce8f;line-height:2">
    admin &nbsp;&nbsp;&nbsp;&nbsp;→ invesmate@2024 &nbsp;(Admin)<br>
    analyst &nbsp;→ analyst@123 &nbsp;&nbsp;&nbsp;(Viewer)<br>
    manager &nbsp;→ manager@123 &nbsp;&nbsp;&nbsp;(Viewer)
  </div>
  <div style="margin-top:12px;font-size:11px;color:#4a5068;line-height:1.7">
    ⚠️ Users added via this panel persist for the current session only.<br>
    To make permanent: add them to the <strong style="color:#eceef5">USERS</strong> dict in
    <strong style="color:#eceef5">app.py</strong> or use Streamlit's
    <strong style="color:#eceef5">st.secrets</strong>.
  </div>
</div>
</div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login()
else:
    page = st.session_state.page
    if   page == 'home':      show_home()
    elif page == 'dashboard': show_dashboard()
    elif page == 'admin':     show_admin()
    else:                     show_home()
