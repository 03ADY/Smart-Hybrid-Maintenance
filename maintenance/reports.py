"""HTML executive report for stakeholder export."""

from datetime import datetime

from maintenance.config import APP_NAME


def html_executive_report(brief_md: str, summary: dict, roi: dict) -> str:
    """Convert key metrics into a printable HTML brief."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{APP_NAME} Report</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; color: #0f172a; }}
h1 {{ color: #0f766e; }} .kpi {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; }}
.card {{ background: #f1f5f9; padding: 1rem; border-radius: 8px; }}
.warn {{ color: #b45309; }} .crit {{ color: #b91c1c; }}
pre {{ white-space: pre-wrap; background: #f8fafc; padding: 1rem; border-radius: 8px; }}
</style></head><body>
<h1>{APP_NAME}</h1>
<p>Generated {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
<div class="kpi">
  <div class="card"><strong>Avg health</strong><br>{summary.get('avg_health', 0):.1%}</div>
  <div class="card crit"><strong>Critical</strong><br>{summary.get('critical', 0)}</div>
  <div class="card warn"><strong>Warning</strong><br>{summary.get('warning', 0)}</div>
  <div class="card"><strong>Net ROI</strong><br>${roi.get('net_benefit', 0):,.0f}</div>
</div>
<h2>Executive summary</h2>
<pre>{brief_md}</pre>
</body></html>"""
