from __future__ import annotations

import json
import os

import httpx
import streamlit as st

API_BASE = os.getenv("XS_API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="X-SENTINEL", layout="wide")
st.title("X-SENTINEL — Cross-View Backdoor Detection")
st.caption("Product-first baseline · per-file inference-time · EMBER static features")

# Sidebar Authentication Configuration (Finding 15)
st.sidebar.header("Configuration")
api_token = st.sidebar.text_input(
    "API Bearer Token",
    type="password",
    value=os.getenv("XS_API_TOKEN", ""),
    help="Optional bearer token for authenticated backend environments.",
)


def get_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_token.strip():
        headers["Authorization"] = f"Bearer {api_token.strip()}"
    return headers


try:
    health = httpx.get(f"{API_BASE}/health", headers=get_headers(), timeout=3.0).json()
    if health.get("demo_mode"):
        st.warning("DEMO MODE — outputs are integration placeholders, not scientific evidence.")
    st.success("Backend connected")
except Exception as exc:
    st.error(f"Backend unavailable: {exc}")
    st.stop()

st.subheader("Analyze EMBER vector")
source_name = st.text_input("Source/sample name", value="demo-sample")
text = st.text_area(
    "Vector JSON",
    value=json.dumps([0.0] * 2381),
    height=180,
    help="Exactly 2,381 numeric features are required.",
)

if st.button("Analyze", type="primary"):
    try:
        features = json.loads(text)
        response = httpx.post(
            f"{API_BASE}/v1/analyze/vector",
            json={"features": features, "source_name": source_name},
            headers=get_headers(),
            timeout=30.0,
        )
        if response.status_code != 200:
            st.error(response.text)
        else:
            data = response.json()
            st.subheader(data["status"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Malware score", f'{data["malware_score"]:.4f}')
            c2.metric("Suspicion score", f'{data["suspicion_score"]:.4f}')
            c3.metric("Threshold", "N/A" if data["threshold"] is None else data["threshold"])
            st.write("Signals", data["signals"])
            st.write("View contributions", data["view_contributions"])
            st.json(data)
            st.download_button(
                "Download evidence JSON",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f'{data["request_id"]}.json',
                mime="application/json",
            )
    except Exception as exc:
        st.exception(exc)

st.divider()
st.subheader("System readiness")
try:
    st.json(httpx.get(f"{API_BASE}/ready", headers=get_headers(), timeout=3.0).json())
except Exception as exc:
    st.error(str(exc))
