#!/usr/bin/env python3
"""
BRAINAI5 V3 — HTML Dashboard Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stdlib only (no pip needed). Generates a Chart.js dashboard
from a research JSON report.

Usage:
  python dashboard_gen.py output/reports/2026-03-29-betrayal-karma.json
Output:
  output/dashboards/2026-03-29-betrayal-karma.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _esc(text: str) -> str:
    """Escape HTML special chars for safe embedding."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate(data: dict, out_dir: Path) -> Path:
    niche    = data.get("niche", "Unknown")
    today    = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    slug     = data.get("slug", slugify(niche))
    stats    = data.get("stats", {})
    creators = data.get("creators", [])[:6]
    formats  = data.get("formats", [])[:6]
    bo       = data.get("blue_ocean", [])[:5]

    # ── Chart.js data ──
    creator_names = json.dumps([c.get("name", "") for c in creators])
    creator_subs  = json.dumps([c.get("subs", 0) for c in creators])
    format_labels = json.dumps([f.get("name", "") for f in formats])
    format_views  = json.dumps([f.get("avg_views", 0) for f in formats])

    # ── Saturation badge ──
    sat = stats.get("saturation", "?")
    sat_lower = sat.lower()
    if sat_lower == "blue":
        sat_color, sat_bg = "#60a5fa", "#003d8f"
    elif sat_lower == "orange":
        sat_color, sat_bg = "#fb923c", "#7c2d12"
    else:
        sat_color, sat_bg = "#f87171", "#450a0a"

    # ── Blue ocean opportunity cards ──
    opp_cards = ""
    for o in bo:
        opp_cards += (
            f'<div class="opp">'
            f'<div class="opp-name">{_esc(o.get("name", ""))}</div>'
            f'<div class="opp-meta">'
            f'RPM: <b>${_esc(o.get("rpm_est", "?"))}</b> &nbsp;&middot;&nbsp; '
            f'Effort: <b>{_esc(o.get("effort_hours", "?"))}h</b> &nbsp;&middot;&nbsp; '
            f'Barrier: <b>{_esc(o.get("entry_barrier", "?"))}</b>'
            f'</div>'
            f'<div class="opp-why">{_esc(o.get("why", "")[:160])}</div>'
            f'</div>\n'
        )

    # ── Creator table rows ──
    creator_rows = ""
    for c in creators:
        creator_rows += (
            f"<tr>"
            f"<td>{_esc(c.get('name',''))}</td>"
            f"<td>{_esc(c.get('platform','YouTube'))}</td>"
            f"<td>{_esc(c.get('subs',''))}</td>"
            f"<td>{_esc(c.get('growth_rate_12mo',''))}</td>"
            f"<td>${_esc(c.get('est_monthly_rev',''))}</td>"
            f"<td>{_esc(c.get('format_innovation','')[:60])}</td>"
            f"</tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BRAINAI5 &mdash; {_esc(niche)}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0a0a;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:20px 24px;max-width:1400px;margin:0 auto}}
h1{{color:#00d4ff;font-size:1.5rem;margin-bottom:4px}}
.meta{{color:#555;font-size:.8rem;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:20px}}
.card{{background:#141414;border:1px solid #222;border-radius:10px;padding:18px}}
.card h2{{color:#00d4ff;font-size:.85rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}}
.stat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.stat{{background:#0a0a0a;border-radius:7px;padding:10px}}
.stat-label{{color:#555;font-size:.72rem;margin-bottom:3px}}
.stat-value{{color:#fff;font-size:1.1rem;font-weight:700}}
.badge{{display:inline-block;padding:2px 12px;border-radius:999px;font-size:.73rem;font-weight:600;background:{sat_bg};color:{sat_color}}}
.opp{{background:#0a0a0a;border-left:3px solid #00d4ff;border-radius:0 6px 6px 0;padding:10px 12px;margin-bottom:10px}}
.opp-name{{color:#fff;font-weight:600;font-size:.9rem;margin-bottom:4px}}
.opp-meta{{color:#00d4ff;font-size:.75rem;margin-bottom:4px}}
.opp-why{{color:#888;font-size:.78rem;line-height:1.4}}
canvas{{max-height:220px}}
.summary-card{{background:#141414;border-radius:10px;padding:16px;border-left:3px solid #7c3aed;color:#ccc;font-size:.88rem;line-height:1.6}}
.summary-card b{{color:#a78bfa}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{color:#555;text-align:left;padding:6px 8px;border-bottom:1px solid #222;font-weight:600;font-size:.75rem;text-transform:uppercase}}
td{{padding:7px 8px;border-bottom:1px solid #1a1a1a;color:#ccc}}
tr:hover td{{background:#1a1a1a}}
</style>
</head>
<body>

<h1>&#x1F9E0; BRAINAI5 &mdash; {_esc(niche)}</h1>
<div class="meta">
  Research: {_esc(today)} &nbsp;&middot;&nbsp;
  Category: {_esc(data.get('category','?'))} &nbsp;&middot;&nbsp;
  Query: &ldquo;{_esc(data.get('query',''))}&rdquo;
</div>

<div class="grid">

  <!-- NICHE STATS -->
  <div class="card">
    <h2>&#x1F4CA; Niche Stats</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="stat-label">Growth Rate</div>
        <div class="stat-value">{_esc(stats.get('growth_rate','?'))}x/yr</div>
      </div>
      <div class="stat">
        <div class="stat-label">CPM Range</div>
        <div class="stat-value">${_esc(stats.get('cpm_low','?'))}&ndash;${_esc(stats.get('cpm_high','?'))}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Monthly Audience</div>
        <div class="stat-value">{_esc(stats.get('audience_m','?'))}M</div>
      </div>
      <div class="stat">
        <div class="stat-label">Saturation</div>
        <div class="stat-value"><span class="badge">{_esc(sat)} Ocean</span></div>
      </div>
      <div class="stat">
        <div class="stat-label">Entry Barrier</div>
        <div class="stat-value">{_esc(stats.get('entry_barrier','?'))}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Blue Ocean Gaps</div>
        <div class="stat-value">{len(bo)}</div>
      </div>
    </div>
  </div>

  <!-- CREATOR CHART -->
  <div class="card">
    <h2>&#x1F3C6; Top Creators (Subscribers)</h2>
    <canvas id="creatorChart"></canvas>
  </div>

  <!-- FORMAT CHART -->
  <div class="card">
    <h2>&#x1F3AC; Format Performance (Avg Views)</h2>
    <canvas id="formatChart"></canvas>
  </div>

  <!-- BLUE OCEAN -->
  <div class="card">
    <h2>&#x1F30A; Blue Ocean Gaps</h2>
    {opp_cards if opp_cards else '<p style="color:#555;font-size:.85rem">No gaps identified</p>'}
  </div>

</div>

<!-- CREATOR TABLE -->
<div class="card" style="margin-bottom:20px">
  <h2>&#x1F465; Creator Breakdown</h2>
  <table>
    <thead><tr><th>Name</th><th>Platform</th><th>Subscribers</th><th>Growth 12mo</th><th>Est. Rev/mo</th><th>Innovation</th></tr></thead>
    <tbody>{creator_rows}</tbody>
  </table>
</div>

<!-- SUMMARY -->
<div class="summary-card">
  <b>&#x1F4A1; Research Summary</b><br><br>
  {_esc(data.get('summary',''))}
</div>

<script>
const chartDefaults = {{
  plugins: {{ legend: {{ display: false }} }},
  scales: {{
    x: {{ ticks: {{ color: '#666', font: {{ size: 10 }} }}, grid: {{ color: '#1a1a1a' }} }},
    y: {{ ticks: {{ color: '#666' }}, grid: {{ color: '#1a1a1a' }} }}
  }}
}};

new Chart(document.getElementById('creatorChart'), {{
  type: 'bar',
  data: {{
    labels: {creator_names},
    datasets: [{{ label: 'Subscribers', data: {creator_subs}, backgroundColor: '#00d4ff44', borderColor: '#00d4ff', borderWidth: 2 }}]
  }},
  options: chartDefaults
}});

new Chart(document.getElementById('formatChart'), {{
  type: 'bar',
  data: {{
    labels: {format_labels},
    datasets: [{{ label: 'Avg Views', data: {format_views}, backgroundColor: '#7c3aed44', borderColor: '#7c3aed', borderWidth: 2 }}]
  }},
  options: {{ ...chartDefaults, indexAxis: 'y' }}
}});
</script>

</body>
</html>"""

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{today}-{slug}.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"[DASHBOARD] Saved: {out_file}", flush=True)
    return out_file


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dashboard_gen.py <path-to-report.json>")
        sys.exit(1)
    report_file = Path(sys.argv[1])
    if not report_file.exists():
        print(f"ERROR: File not found: {report_file}")
        sys.exit(1)
    report_data = json.loads(report_file.read_text(encoding="utf-8"))
    out = Path(__file__).parent / "output" / "dashboards"
    generate(report_data, out)
