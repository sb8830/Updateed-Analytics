"""
ms365_connector.py  —  SharePoint connector using Microsoft account credentials
Uses ROPC (Resource Owner Password Credentials) flow — no Azure Portal setup needed
beyond the built-in Microsoft Office app client ID.

Secrets needed in Streamlit Cloud:
  MS_EMAIL    = "admin@admininvesmate360.onmicrosoft.com"
  MS_PASSWORD = "your-microsoft-password"

File URLs are hardcoded from your SharePoint links.
"""

import io
import re
import requests
import streamlit as st

# ── Your SharePoint tenant & files (hardcoded from your URLs) ─────────────────
_TENANT     = "admininvesmate360.onmicrosoft.com"
_SP_HOST    = "admininvesmate360-my.sharepoint.com"

# Microsoft Office public client ID (works for any M365 tenant, no registration needed)
_CLIENT_ID  = "d3590ed6-52b3-4102-aeff-aad2292ab01c"   # Microsoft Office

_FILES = {
    "webinar": {
        "name":    "Free Class Lead Report.xlsx",
        "user":    "admin_admininvesmate360_onmicrosoft_com",
        "item_id": "B4E16F58-734E-403A-8F5E-3E60656AF593",
    },
    "seminar": {
        "name":    "Offline Seminar Report.xlsx",
        "user":    "admin_admininvesmate360_onmicrosoft_com",
        "item_id": "A4283220-7EF3-49B5-87DD-B7FD023D436D",
    },
    "attendee": {
        "name":    "Offline Indepth Details.xlsx",
        "user":    "sourajpal_invesmate_com",
        "share_encoded": "IQBF8dCDEjW_QrTvqVmFzIP0AZazBviXK0FEtIbUsgch6V0",
        "share_token":   "wy3zM6",
    },
}

# ─── GET ACCESS TOKEN via username + password ─────────────────────────────────
def _get_token() -> str:
    """
    ROPC flow — authenticates with Microsoft using email + password.
    No Azure app registration required; uses Microsoft Office's built-in client.
    """
    try:
        email    = st.secrets["MS_EMAIL"].strip()
        password = st.secrets["MS_PASSWORD"].strip()
    except KeyError as e:
        raise ConnectionError(
            f"❌ Missing secret: {e}\n"
            "Add MS_EMAIL and MS_PASSWORD to Streamlit Cloud Secrets."
        )

    url  = f"https://login.microsoftonline.com/{_TENANT}/oauth2/v2.0/token"
    data = {
        "grant_type": "password",
        "client_id":  _CLIENT_ID,
        "username":   email,
        "password":   password,
        "scope":      "https://graph.microsoft.com/.default offline_access",
    }

    resp = requests.post(url, data=data, timeout=15)
    body = resp.json()

    if resp.status_code != 200:
        err = body.get("error_description", body.get("error", resp.text))
        # Common errors with helpful messages
        if "AADSTS50126" in err or "AADSTS50034" in err:
            raise ConnectionError(
                "❌ Wrong email or password.\n"
                "Check MS_EMAIL and MS_PASSWORD in Streamlit Secrets."
            )
        if "AADSTS53003" in err or "conditional" in err.lower():
            raise ConnectionError(
                "❌ Conditional Access policy is blocking sign-in.\n"
                "Your IT admin has restricted password-based login.\n"
                "Ask your admin to exclude this app from the Conditional Access policy,\n"
                "or use the Azure App Registration method instead."
            )
        if "AADSTS7000218" in err:
            raise ConnectionError(
                "❌ Client not allowed to use ROPC flow.\n"
                "Enable 'Allow public client flows' in your Azure App Registration,\n"
                "or use the admin's personal Microsoft credentials."
            )
        raise ConnectionError(f"❌ Authentication failed:\n{err}")

    return body["access_token"]


# ─── DOWNLOAD FILE ────────────────────────────────────────────────────────────
def _download(token: str, file_key: str) -> io.BytesIO:
    meta    = _FILES[file_key]
    name    = meta["name"]
    headers = {"Authorization": f"Bearer {token}"}

    # ── Files 1 & 2: use item ID in admin's OneDrive ──────────────────────────
    if "item_id" in meta:
        user    = meta["user"]
        item_id = meta["item_id"]

        # Primary: by item ID
        url  = f"https://graph.microsoft.com/v1.0/users/{user}/drive/items/{item_id}/content"
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)

        if resp.status_code == 200 and _is_excel(resp):
            return io.BytesIO(resp.content)

        # Fallback: search by filename
        if resp.status_code in (404, 403):
            q    = requests.utils.quote(name)
            surl = f"https://graph.microsoft.com/v1.0/users/{user}/drive/root/search(q='{q}')"
            sr   = requests.get(surl, headers=headers, timeout=15)
            if sr.status_code == 200:
                items = sr.json().get("value", [])
                match = next((i for i in items
                              if i.get("name","").lower() == name.lower()), None)
                if match:
                    dl   = requests.get(
                        f"https://graph.microsoft.com/v1.0/users/{user}/drive/items/{match['id']}/content",
                        headers=headers, timeout=30, allow_redirects=True
                    )
                    if dl.status_code == 200 and _is_excel(dl):
                        return io.BytesIO(dl.content)

        _raise_error(resp, name)

    # ── File 3: use share link (Sourajpal's OneDrive) ─────────────────────────
    else:
        share_enc   = meta["share_encoded"]
        share_token = meta["share_token"]

        # Method A: Graph shares endpoint with encoded share ID
        url_a = f"https://graph.microsoft.com/v1.0/shares/{share_enc}/driveItem/content"
        resp  = requests.get(url_a, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code == 200 and _is_excel(resp):
            return io.BytesIO(resp.content)

        # Method B: re-encode the share URL properly
        import base64
        share_url   = f"https://{_SP_HOST}/:x:/g/personal/{meta['user']}/{share_enc}?e={share_token}"
        encoded     = base64.urlsafe_b64encode(("u!" + share_url).encode()).decode().rstrip("=")
        url_b       = f"https://graph.microsoft.com/v1.0/shares/{encoded}/driveItem/content"
        resp2       = requests.get(url_b, headers=headers, timeout=30, allow_redirects=True)
        if resp2.status_code == 200 and _is_excel(resp2):
            return io.BytesIO(resp2.content)

        # Method C: access via Sourajpal's drive directly
        user  = meta["user"]
        q     = requests.utils.quote("Offline Indepth Details")
        surl  = f"https://graph.microsoft.com/v1.0/users/{user}/drive/root/search(q='{q}')"
        sr    = requests.get(surl, headers=headers, timeout=15)
        if sr.status_code == 200:
            items = sr.json().get("value", [])
            if items:
                dl = requests.get(
                    f"https://graph.microsoft.com/v1.0/users/{user}/drive/items/{items[0]['id']}/content",
                    headers=headers, timeout=30, allow_redirects=True
                )
                if dl.status_code == 200 and _is_excel(dl):
                    return io.BytesIO(dl.content)

        _raise_error(resp, name)


def _is_excel(resp) -> bool:
    ct = resp.headers.get("Content-Type", "")
    return (
        "spreadsheet" in ct or
        "octet-stream" in ct or
        "excel" in ct or
        resp.content[:4] == b'PK\x03\x04'
    )


def _raise_error(resp, name: str):
    s = resp.status_code
    if s == 401:
        raise PermissionError(
            f"❌ Not authorised to access '{name}'.\n"
            "Make sure MS_EMAIL has access to this file in SharePoint."
        )
    if s == 403:
        raise PermissionError(
            f"❌ Access denied for '{name}' (403).\n"
            "The logged-in account doesn't have permission to read this file."
        )
    if s == 404:
        raise FileNotFoundError(
            f"❌ File '{name}' not found (404).\n"
            "The file may have been moved or renamed."
        )
    raise RuntimeError(
        f"❌ Failed to download '{name}': HTTP {s}\n{resp.text[:200]}"
    )


# ─── MAIN ENTRY ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=0, show_spinner=False)
def fetch_excel_files(_cache_bust: int = 0) -> dict:
    """
    Fetch all 3 Excel files using Microsoft account credentials.
    Credentials are read from Streamlit Secrets.
    """
    token   = _get_token()
    results = {}
    for key in _FILES:
        results[key] = _download(token, key)
    return results


# ─── SECRETS CHECK ────────────────────────────────────────────────────────────
def check_secrets_configured() -> tuple:
    missing = []
    try:
        for k in ["MS_EMAIL", "MS_PASSWORD"]:
            if not st.secrets.get(k, "").strip():
                missing.append(k)
    except Exception:
        missing = ["MS_EMAIL", "MS_PASSWORD"]
    return len(missing) == 0, missing
