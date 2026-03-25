"""
ms365_connector.py  —  SharePoint Direct Download (No Azure needed!)

How it works:
  SharePoint "Anyone with link" share URLs can be downloaded directly
  by appending &download=1 — no authentication required.

SETUP (one-time, 2 minutes per file):
  For each Excel file in OneDrive/SharePoint:
  1. Right-click the file → Share
  2. Change permissions to "Anyone with the link can view"
  3. Click "Copy link"
  4. Paste the link into Streamlit Secrets

  Then in Streamlit Cloud → App Settings → Secrets, add:
    SHARE_URL_WEBINAR  = "https://admininvesmate360-my.sharepoint.com/..."
    SHARE_URL_SEMINAR  = "https://admininvesmate360-my.sharepoint.com/..."
    SHARE_URL_ATTENDEE = "https://admininvesmate360-my.sharepoint.com/..."

  When a team member updates the file, just click Refresh — 
  the dashboard fetches the latest version automatically.

NOTE: The share URLs are stored in secrets (not in code) so they're
      private and can be updated without redeploying.
"""

import io
import re
import requests
import streamlit as st

# ─── Secret keys ──────────────────────────────────────────────────────────────
_SECRET_KEYS = {
    "webinar":  "SHARE_URL_WEBINAR",
    "seminar":  "SHARE_URL_SEMINAR",
    "attendee": "SHARE_URL_ATTENDEE",
}

_FILE_NAMES = {
    "webinar":  "Free Class Lead Report.xlsx",
    "seminar":  "Offline Seminar Report.xlsx",
    "attendee": "Offline Indepth Details.xlsx",
}

# ─── URL → Download URL conversion ────────────────────────────────────────────
def _to_download_url(share_url: str) -> str:
    """
    Convert any SharePoint/OneDrive share URL to a direct download URL.

    Handles all common SharePoint URL formats:
    - /Doc.aspx?sourcedoc={GUID}&...
    - /:x:/g/personal/.../ENCODED_ID?e=TOKEN
    - /:x:/r/personal/.../ENCODED_ID?e=TOKEN
    - 1drv.ms short links
    """
    url = share_url.strip()

    # Already a download URL
    if "download=1" in url or "/download?" in url:
        return url

    # Format 1: Doc.aspx with sourcedoc GUID
    # Convert to direct download via UniqueId
    m = re.search(r'sourcedoc=%7B([A-F0-9\-]+)%7D', url, re.I)
    if m:
        guid = m.group(1)
        # Extract host and user path
        host_m = re.search(r'https://([^/]+)', url)
        user_m = re.search(r'/personal/([^/]+)/', url)
        if host_m and user_m:
            host = host_m.group(1)
            user = user_m.group(1)
            return (f"https://{host}/personal/{user}/_layouts/15/download.aspx"
                    f"?UniqueId={guid}")

    # Format 2: Share link with ?e=TOKEN — append &download=1
    if "?e=" in url:
        return url + "&download=1"

    # Format 3: Any other SharePoint URL — try appending download=1
    if "sharepoint.com" in url or "1drv.ms" in url:
        sep = "&" if "?" in url else "?"
        return url + sep + "download=1"

    return url


# ─── Download a single file ───────────────────────────────────────────────────
def _download_file(share_url: str, name: str) -> io.BytesIO:
    """Download a file from a SharePoint share URL."""
    dl_url  = _to_download_url(share_url)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept":     "application/octet-stream,*/*",
    }

    resp = requests.get(dl_url, headers=headers, timeout=30, allow_redirects=True)

    # Check if we got an actual Excel file
    content_type = resp.headers.get("Content-Type", "")
    if resp.status_code == 200 and (
        "spreadsheet" in content_type or
        "octet-stream" in content_type or
        "excel" in content_type or
        resp.content[:4] == b'PK\x03\x04'   # ZIP magic bytes (xlsx is a zip)
    ):
        return io.BytesIO(resp.content)

    # Got HTML (login page) — file is not publicly shared
    if resp.status_code == 200 and "text/html" in content_type:
        raise PermissionError(
            f"❌ '{name}' returned a login page instead of the file.\n\n"
            f"The file is not publicly shared. Please:\n"
            f"1. Open the file in OneDrive/SharePoint\n"
            f"2. Click Share → change to 'Anyone with the link can view'\n"
            f"3. Copy the new link and update SHARE_URL_{name.upper()} in Streamlit Secrets."
        )

    if resp.status_code == 403:
        raise PermissionError(
            f"❌ Access denied for '{name}' (403).\n"
            f"Make sure the file is shared as 'Anyone with the link can view'."
        )

    if resp.status_code == 404:
        raise FileNotFoundError(
            f"❌ File '{name}' not found (404).\n"
            f"The share link may have expired or been deleted.\n"
            f"Generate a new share link and update the secret."
        )

    raise RuntimeError(
        f"❌ Failed to download '{name}': HTTP {resp.status_code}\n"
        f"URL tried: {dl_url[:100]}"
    )


# ─── MAIN ENTRY ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=0, show_spinner=False)
def fetch_excel_files(_cache_bust: int = 0) -> dict:
    """
    Fetch all 3 Excel files from SharePoint share URLs.
    URLs are read from Streamlit Secrets.
    Pass a changing _cache_bust to force re-fetch.
    """
    results = {}
    for key, secret_key in _SECRET_KEYS.items():
        name = _FILE_NAMES[key]
        try:
            share_url = st.secrets[secret_key]
        except KeyError:
            raise ValueError(
                f"❌ Secret '{secret_key}' not found.\n"
                f"Go to Streamlit Cloud → App Settings → Secrets and add:\n"
                f"  {secret_key} = \"your-sharepoint-share-url\""
            )

        if not share_url or not share_url.strip().startswith("http"):
            raise ValueError(
                f"❌ '{secret_key}' is empty or invalid.\n"
                f"It should be a SharePoint share URL starting with https://"
            )

        results[key] = _download_file(share_url.strip(), key)

    return results


# ─── SECRETS CHECK ────────────────────────────────────────────────────────────
def check_secrets_configured() -> tuple:
    """Returns (all_ok: bool, missing_keys: list)."""
    missing = []
    try:
        for k in _SECRET_KEYS.values():
            v = st.secrets.get(k, "")
            if not v or not str(v).strip().startswith("http"):
                missing.append(k)
    except Exception:
        missing = list(_SECRET_KEYS.values())
    return len(missing) == 0, missing
