$Root = Split-Path $PSScriptRoot -Parent
$Py = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { python -m venv (Join-Path $Root "venv"); & (Join-Path $Root "venv\Scripts\pip.exe") install -r (Join-Path $Root "requirements.txt") }
if (-not (Test-Path (Join-Path $Root "health_model.h5"))) { & $Py (Join-Path $Root "train.py") }
& $Py (Join-Path $Root "scripts\seed_demo.py")
Start-Process "http://127.0.0.1:8504"
& $Py -m streamlit run (Join-Path $Root "app.py") --server.port 8504
