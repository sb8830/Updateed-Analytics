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

LOGO_B64  = "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"
LOGO_SRC  = "data:image/png;base64," + LOGO_B64
LOGO_HTML = (
    f'<img src="{LOGO_SRC}" style="width:38px;height:38px;border-radius:50%;'
    f'object-fit:cover;border:2px solid rgba(79,206,143,.4);flex-shrink:0">'
)

# ──────────────────────────────────────────────────────────────────────────────
# AUTH CONFIG
# ──────────────────────────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

USERS = {
    "admin":   {"hash": _hash("invesmate@2024"), "role": "admin",  "name": "Admin",    "suspended": False, "reset_token": ""},
    "analyst": {"hash": _hash("analyst@123"),    "role": "viewer", "name": "Analyst",  "suspended": False, "reset_token": ""},
    "manager": {"hash": _hash("manager@123"),    "role": "viewer", "name": "Manager",  "suspended": False, "reset_token": ""},
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
                if user.get('suspended', False):
                    st.error("🚫 Your account has been suspended. Contact admin.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.username  = username.strip().lower()
                    st.session_state.role      = user['role']
                    st.session_state.user_name = user['name']
                    st.session_state.page      = 'home'
                    st.rerun()
            else:
                st.error("❌ Invalid credentials. Try again.")
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
.adm-wrap{{max-width:1060px;margin:0 auto;padding:28px 24px 60px}}
.adm-hdr{{display:flex;align-items:center;gap:14px;margin-bottom:26px}}
.adm-title{{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#eceef5}}
.adm-sub{{font-size:11px;color:#4a5068;margin-top:2px}}
.adm-sec{{background:#0c1018;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:22px 24px;margin-bottom:18px}}
.adm-sec-title{{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;color:#f7c948;
  margin-bottom:16px;text-transform:uppercase;letter-spacing:.8px;display:flex;align-items:center;gap:7px}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}}
.stat-card{{background:#111520;border:1px solid rgba(255,255,255,.06);border-radius:12px;
  padding:16px 18px;position:relative;overflow:hidden}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--c,#4f8ef7)}}
.stat-v{{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#eceef5;line-height:1}}
.stat-l{{font-size:10px;color:#4a5068;text-transform:uppercase;letter-spacing:.6px;margin-top:6px}}
.ut-head{{display:grid;grid-template-columns:1.8fr 1fr 0.8fr 0.8fr 2.6fr;gap:10px;
  padding:8px 14px;background:#111520;border-radius:8px;margin-bottom:6px}}
.ut-head span{{font-size:9px;font-weight:700;color:#4a5068;text-transform:uppercase;letter-spacing:.7px}}
.ut-row{{display:grid;grid-template-columns:1.8fr 1fr 0.8fr 0.8fr 2.6fr;gap:10px;
  padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.04);align-items:center}}
.ut-row:last-child{{border-bottom:none}}
.ut-row:hover{{background:rgba(255,255,255,.02);border-radius:8px}}
.uname{{font-size:13px;font-weight:600;color:#eceef5}}
.umeta{{font-size:10px;color:#4a5068;margin-top:1px}}
.badg{{border-radius:8px;padding:2px 8px;font-size:10px;font-weight:700;display:inline-block}}
.badg-a{{background:rgba(247,201,72,.1);border:1px solid rgba(247,201,72,.2);color:#f7c948}}
.badg-v{{background:rgba(79,142,247,.1);border:1px solid rgba(79,142,247,.2);color:#4f8ef7}}
.badg-s{{background:rgba(247,111,79,.1);border:1px solid rgba(247,111,79,.2);color:#f76f4f}}
.badg-ok{{background:rgba(79,206,143,.1);border:1px solid rgba(79,206,143,.2);color:#4fce8f}}
.reset-token-box{{background:#060910;border:1px solid rgba(247,201,72,.2);border-radius:8px;
  padding:10px 14px;margin-top:8px;font-family:monospace;font-size:12px;color:#f7c948;word-break:break-all}}
</style>
<div class="adm-wrap">
  <div class="adm-hdr">
    {logo_sm}
    <div>
      <div class="adm-title">Admin Panel</div>
      <div class="adm-sub">Manage users, credentials and access control</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="adm-wrap">', unsafe_allow_html=True)

    # ── System Stats ──────────────────────────────────────────────────────────
    total_users    = len(USERS)
    active_users   = sum(1 for u in USERS.values() if not u.get('suspended', False))
    suspended_users= total_users - active_users
    admin_users    = sum(1 for u in USERS.values() if u['role'] == 'admin')

    st.markdown(f"""<div class="adm-sec">
  <div class="adm-sec-title">📊 System Overview</div>
  <div class="stat-grid">
    <div class="stat-card" style="--c:#4f8ef7"><div class="stat-v">{total_users}</div><div class="stat-l">Total Users</div></div>
    <div class="stat-card" style="--c:#4fce8f"><div class="stat-v">{active_users}</div><div class="stat-l">Active</div></div>
    <div class="stat-card" style="--c:#f76f4f"><div class="stat-v">{suspended_users}</div><div class="stat-l">Suspended</div></div>
    <div class="stat-card" style="--c:#f7c948"><div class="stat-v">{admin_users}</div><div class="stat-l">Admins</div></div>
    <div class="stat-card" style="--c:#b44fe7"><div class="stat-v">3</div><div class="stat-l">Dashboards</div></div>
    <div class="stat-card" style="--c:#4fd8f7"><div class="stat-v">8</div><div class="stat-l">Dashboard Tabs</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── User Management Table ─────────────────────────────────────────────────
    st.markdown('''<div class="adm-sec">
  <div class="adm-sec-title">👥 User Management</div>
  <div class="ut-head">
    <span>User</span><span>Role</span><span>Status</span>
    <span>Actions</span><span></span>
  </div>''', unsafe_allow_html=True)

    for uname, ud in list(USERS.items()):
        is_suspended = ud.get('suspended', False)
        is_self      = uname == st.session_state.username
        role_badge   = f'<span class="badg badg-a">Admin</span>' if ud['role']=='admin' else f'<span class="badg badg-v">Viewer</span>'
        status_badge = f'<span class="badg badg-s">Suspended</span>' if is_suspended else f'<span class="badg badg-ok">Active</span>'

        st.markdown(f"""<div class="ut-row">
  <div>
    <div class="uname">{ud['name']} {'<span style="font-size:10px;color:#4fce8f">(you)</span>' if is_self else ''}</div>
    <div class="umeta">@{uname}</div>
  </div>
  <div>{role_badge}</div>
  <div>{status_badge}</div>
  <div></div><div></div>
</div>""", unsafe_allow_html=True)

        # Action buttons for each user
        cols = st.columns([1.8, 1, 0.8, 0.8, 0.65, 0.65, 0.65, 0.65])
        # col offset to align under "Actions" column
        with cols[4]:
            # Toggle suspend (can't suspend yourself)
            if not is_self:
                susp_label = "▶ Activate" if is_suspended else "⏸ Suspend"
                if st.button(susp_label, key=f"susp_{uname}", use_container_width=True):
                    USERS[uname]['suspended'] = not is_suspended
                    action = "activated" if is_suspended else "suspended"
                    st.success(f"✅ {ud['name']} {action}.")
                    st.rerun()

        with cols[5]:
            # Toggle role (can't change own role)
            if not is_self:
                new_role = "admin" if ud['role'] == "viewer" else "viewer"
                role_btn = "→ Admin" if new_role == "admin" else "→ Viewer"
                if st.button(role_btn, key=f"role_{uname}", use_container_width=True):
                    USERS[uname]['role'] = new_role
                    st.success(f"✅ {ud['name']} is now {new_role}.")
                    st.rerun()

        with cols[6]:
            # Generate reset token
            import secrets
            if st.button("🔑 Reset", key=f"rst_{uname}", use_container_width=True):
                token = secrets.token_urlsafe(12)
                USERS[uname]['reset_token'] = token
                st.session_state[f'show_token_{uname}'] = token
                st.rerun()

        with cols[7]:
            # Delete user (can't delete yourself or last admin)
            admin_count = sum(1 for u in USERS.values() if u['role'] == 'admin')
            can_delete  = not is_self and not (ud['role'] == 'admin' and admin_count <= 1)
            if can_delete:
                if st.button("🗑 Delete", key=f"del_{uname}", use_container_width=True):
                    st.session_state[f'confirm_del_{uname}'] = True
                    st.rerun()

        # Show reset token if generated
        if st.session_state.get(f'show_token_{uname}'):
            token_val = st.session_state[f'show_token_{uname}']
            st.markdown(f'''<div class="reset-token-box">
  🔑 Temporary reset token for <strong>{uname}</strong>:<br>
  <strong>{token_val}</strong><br>
  <span style="font-size:10px;color:#4a5068;font-family:'DM Sans',sans-serif">
  Share this token with the user. They must change password after logging in.</span>
</div>''', unsafe_allow_html=True)
            if st.button(f"✖ Dismiss", key=f"dis_{uname}"):
                del st.session_state[f'show_token_{uname}']
                st.rerun()

        # Delete confirmation
        if st.session_state.get(f'confirm_del_{uname}'):
            st.warning(f"⚠️ Delete **{ud['name']}** (@{uname})? This cannot be undone.")
            ca, cb_ = st.columns(2)
            with ca:
                if st.button(f"✅ Yes, delete {uname}", key=f"cd_yes_{uname}", type="primary"):
                    del USERS[uname]
                    if f'confirm_del_{uname}' in st.session_state:
                        del st.session_state[f'confirm_del_{uname}']
                    st.success(f"✅ User {uname} deleted.")
                    st.rerun()
            with cb_:
                if st.button("✖ Cancel", key=f"cd_no_{uname}"):
                    del st.session_state[f'confirm_del_{uname}']
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Add New User ──────────────────────────────────────────────────────────
    st.markdown('<div class="adm-sec"><div class="adm-sec-title">➕ Add New User</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    nu  = c1.text_input("Username",     key="nu",  placeholder="username")
    nn  = c2.text_input("Display Name", key="nn",  placeholder="Full Name")
    np_ = c3.text_input("Password",     key="np_", placeholder="password", type="password")
    nr  = c4.selectbox("Role", ["viewer","admin"], key="nr")
    if st.button("➕ Add User", key="au_btn", type="primary"):
        if nu and nn and np_:
            if nu.lower() in USERS:
                st.warning(f"⚠️ '{nu}' already exists.")
            else:
                USERS[nu.lower()] = {"hash":_hash(np_),"role":nr,"name":nn,"suspended":False,"reset_token":""}
                st.success(f"✅ User '{nu}' added as {nr}.")
                st.rerun()
        else:
            st.warning("Fill all fields.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Change Password ───────────────────────────────────────────────────────
    st.markdown('<div class="adm-sec"><div class="adm-sec-title">🔑 Change Password</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    cpu = c1.selectbox("Select User", list(USERS.keys()), key="cpu")
    cpn = c2.text_input("New Password",     key="cpn", type="password", placeholder="new password")
    cpc = c3.text_input("Confirm Password", key="cpc", type="password", placeholder="confirm")
    if st.button("🔑 Update Password", key="cp_btn", type="primary"):
        if cpn and cpn == cpc:
            USERS[cpu]['hash'] = _hash(cpn)
            USERS[cpu]['reset_token'] = ""
            st.success(f"✅ Password updated for {cpu}.")
        elif cpn != cpc:
            st.error("❌ Passwords don't match.")
        else:
            st.warning("Enter a new password.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Forgot / Reset Password Flow ──────────────────────────────────────────
    st.markdown('<div class="adm-sec"><div class="adm-sec-title">🔐 Forgot Password — Reset Lookup</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px;color:#4a5068;margin-bottom:14px">Enter the reset token given to the user to set a new password.</p>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    rt_token = c1.text_input("Reset Token", key="rt_tok", placeholder="paste token here")
    rt_new   = c2.text_input("New Password", key="rt_new", type="password", placeholder="new password")
    rt_conf  = c3.text_input("Confirm",      key="rt_conf", type="password", placeholder="confirm")
    if st.button("✅ Apply Reset", key="rt_btn", type="primary"):
        matched = next((u for u, ud in USERS.items()
                        if ud.get('reset_token') and ud['reset_token'] == rt_token.strip()), None)
        if not matched:
            st.error("❌ Invalid or expired token.")
        elif not rt_new:
            st.warning("Enter a new password.")
        elif rt_new != rt_conf:
            st.error("❌ Passwords don't match.")
        else:
            USERS[matched]['hash'] = _hash(rt_new)
            USERS[matched]['reset_token'] = ""
            st.success(f"✅ Password reset for @{matched}. Token cleared.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


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
