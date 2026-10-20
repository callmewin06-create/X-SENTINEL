"""Readiness regression with a mock DB, then a localhost-only UI review server."""
import os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
test=subprocess.run([sys.executable,'-X','utf8','-m','pytest',
    'tests/test_history_adapter.py::test_api_readiness_failure_is_visible',
    '-q','-p','no:cacheprovider','--disable-warnings',
    '--junitxml=outputs/implementation_2026_10_20/test_api_readiness.xml'],timeout=90)
if test.returncode:raise SystemExit(test.returncode)
os.environ.pop('XS_API_BASE_URL',None)
from streamlit.web import cli
sys.argv=['streamlit','run','dashboard/app.py','--server.address','127.0.0.1',
          '--server.port','8510','--server.headless','true','--browser.gatherUsageStats','false',
          '--server.fileWatcherType','none']
cli.main()
