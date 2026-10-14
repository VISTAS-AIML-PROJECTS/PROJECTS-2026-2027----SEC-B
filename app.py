import base64
import io
import json
import os
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps

from skin_ai_model import analyze_skin_image
from products_db import get_recommended_products

st.set_page_config(
    page_title="DermaVision AI Mirror",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Full-screen scanner UI (camera + Face Scan / Choose Photo + recommendations + close).
# The UI lives in components/skin_scanner/index.html. Python only runs the analysis.
# ---------------------------------------------------------------------------
_scanner = components.declare_component(
    "skin_scanner",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "components", "skin_scanner"),
)

# Hide all Streamlit chrome and stretch the scanner over the whole browser window.
st.markdown(
    """
<style>
    html, body, [data-testid="stAppViewContainer"], .stApp { background: #05070c !important; overflow: hidden !important; }
    header[data-testid="stHeader"], div[data-testid="stToolbar"], div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"], section[data-testid="stSidebar"],
    div[data-testid="stSidebarCollapsedControl"], #MainMenu, footer { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    iframe[title*="skin_scanner"] {
        position: fixed !important; inset: 0 !important;
        width: 100vw !important; height: 100vh !important;
        border: 0 !important; z-index: 999999 !important; background: #05070c;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _json_safe(obj):
    """Round-trip through JSON so numpy numbers etc. become plain Python types."""
    return json.loads(json.dumps(obj, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


def _run_scan(event):
    """Decode the image sent by the browser, run the existing analysis, and build the panel data."""
    try:
        _, b64 = event["image"].split(",", 1)
        image = Image.open(io.BytesIO(base64.b64decode(b64)))
        image = ImageOps.exif_transpose(image)  # phone photos: honour rotation

        analysis = analyze_skin_image(image, test_mode="auto")
        products = get_recommended_products(analysis["detectedIssues"])

        for p in products:
            q = urllib.parse.quote(f"{p['name']} skincare buy")
            p["buyUrl"] = f"https://www.google.com/search?q={q}"

        return _json_safe({
            "id": event["id"],
            "score": analysis["overallScore"],
            "issues": analysis["detectedIssues"],
            "products": products,
        })
    except Exception as exc:  # show the problem in the panel instead of crashing the page
        return {"id": event.get("id"), "error": f"Could not analyze this image: {exc}"}


ss = st.session_state
ss.setdefault("result", None)
ss.setdefault("last_event_id", None)

event = _scanner(result=ss["result"], key="skin_scanner", default=None)

if isinstance(event, dict) and event.get("id") != ss["last_event_id"]:
    ss["last_event_id"] = event["id"]
    if event.get("action") == "scan" and event.get("image"):
        ss["result"] = _run_scan(event)
    elif event.get("action") == "close":
        ss["result"] = None
    st.rerun()
