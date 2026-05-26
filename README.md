# PredictiveOps Enterprise

Smart hybrid maintenance demo: **LSTM health scoring**, **fleet command center**, **multi-machine simulation**, sensor drivers, work orders, SQLite audit (problems + resolutions persisted), ROI modeling, and executive brief export.

## Features

- **Fleet Command Center** — 10-machine health map, fleet scan, risk ranking, ROI  
- **Live Dashboard** — sensors, driver chart, playbooks, acknowledge/schedule  
- **Historical Explorer** — trends, alert timeline, period compare, MTBF-style gaps  
- **Demo scenarios** — Normal, Plant stress, Cooling failure drill  
- **Present mode** — simplified controls for live demos  
- **Auto-seed** — instant history on first launch  
- **Maintenance Planner** — Gantt + CMMS JSON export  
- **Model Insights** — heatmap, driver aggregates, shift compare  
- **HTML report** — stakeholder-ready export  

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python train.py
.\scripts\start-demo.ps1
```

Reset DB: `python -c "import database; database.init_db(force_reset=True)"`

## Layout

| Path | Role |
|------|------|
| `app.py` | Landing + model card |
| `pages/0_🌐_Fleet_Command_Center.py` | Fleet ops |
| `pages/1_📈_Live_Dashboard.py` | Live machine view |
| `pages/2_🏛️_Historical_Explorer.py` | History & audit |
| `maintenance/` | Core, scenarios, insights, bootstrap |
| `database.py` | SQLite v2 schema |
| `train.py` | LSTM + metadata |
