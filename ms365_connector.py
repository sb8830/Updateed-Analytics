import requests
import streamlit as st
import time

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


# ─────────────────────────────────────────────
# AUTH TOKEN
# ─────────────────────────────────────────────
def get_token():
    return st.secrets["MS365_TOKEN"]  # store token in secrets


# ─────────────────────────────────────────────
# RETRY LOGIC (FIX 429)
# ─────────────────────────────────────────────
def safe_get(url, headers, retries=3):
    for attempt in range(retries):
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            return resp

        if resp.status_code == 429:
            wait = 2 ** attempt
            time.sleep(wait)
            continue

        raise RuntimeError(f"❌ API Error {resp.status_code}: {resp.text[:200]}")

    raise RuntimeError("❌ Max retries exceeded")


# ─────────────────────────────────────────────
# LIST FILES FROM ONEDRIVE
# ─────────────────────────────────────────────
def list_files(token):
    url = f"{GRAPH_BASE}/me/drive/root/children"
    headers = {"Authorization": f"Bearer {token}"}

    resp = safe_get(url, headers)
    return resp.json().get("value", [])


# ─────────────────────────────────────────────
# DOWNLOAD FILE USING FILE ID
# ─────────────────────────────────────────────
def download_file(token, file_id):
    url = f"{GRAPH_BASE}/me/drive/items/{file_id}/content"
    headers = {"Authorization": f"Bearer {token}"}

    resp = safe_get(url, headers)
    return resp.content


# ─────────────────────────────────────────────
# MAIN FETCH FUNCTION (CACHED)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)  # 5 min cache (prevents 429)
def fetch_excel_files(refresh_key=0):

    token = get_token()

    files = list_files(token)

    # DEBUG (optional)
    print("Files in OneDrive:")
    for f in files:
        print(f["name"])

    result = {
        "leads": None,
        "seminar": None,
        "indepth": None
    }

    # SMART MATCHING (no exact filename dependency)
    for f in files:
        name = f["name"].lower()

        if "lead" in name:
            result["leads"] = download_file(token, f["id"])

        elif "seminar" in name or "offline report" in name:
            result["seminar"] = download_file(token, f["id"])

        elif "indepth" in name or "details" in name:
            result["indepth"] = download_file(token, f["id"])

    # VALIDATION
    missing = [k for k, v in result.items() if v is None]
    if missing:
        raise RuntimeError(f"❌ Missing files in OneDrive: {missing}")

    return result
