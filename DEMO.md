# PredictiveOps — 2 min Demo

```powershell
python train.py
.\scripts\start-demo.ps1
```

**http://127.0.0.1:8504** · Data auto-seeds on first run.

## Flow

1. **Landing** — fleet snapshot tiles (pre-seeded)  
2. **Fleet Command** — **Cooling failure drill** → **Run fleet scan**  
3. Critical banner → health map → **Download HTML report**  
4. **Maintenance Planner** — Gantt + **CMMS JSON** export  
5. **Live Dashboard** — M#5, enable **Compare**, sensor anomaly flags  
6. **Model Insights** — fleet heatmap + top drivers  
7. **Historical** — shift compare + alert timeline  

## Highlights

- **OEE scorecard** on landing (availability × performance × quality)  
- **Alert Center** with acknowledge workflow  
- **Spare parts** catalog + fault-based recommendations  
- **Demo tools**: reseed / reset DB in sidebar  
- Auto-seed · sensor anomalies · HTML report · CMMS export · fleet heatmap · machine compare  
