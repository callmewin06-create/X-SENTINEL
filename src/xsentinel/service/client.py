"""Small HTTP client used by Streamlit. No implicit local fallback on save failure."""
import json
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError


def api_request(base, path, payload=None):
    data = json.dumps(payload,allow_nan=False).encode() if payload is not None else None
    req = Request(base.rstrip('/')+path,data=data,headers={'Content-Type':'application/json'})
    try:
        with urlopen(req,timeout=90) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = json.loads(exc.read()).get('detail','Request failed')
        raise RuntimeError(f'API {exc.code}: {detail}') from None
    except (URLError,TimeoutError):
        raise RuntimeError('Cannot reach analysis/history API; no saved result confirmed') from None
