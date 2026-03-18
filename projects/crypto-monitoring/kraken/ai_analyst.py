#!/usr/bin/env python3
"""
YNAI5 AI Portfolio Analyst
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analyzes Kraken portfolio data using Claude Haiku.
Scores urgency 1-10. Sends Telegram alert if urgency >= 7.
Throttles: max 3 AI alerts per day, min 2h between alerts.

Usage:
  python ai_analyst.py              # analyze kraken_portfolio.json, alert if urgent
  python ai_analyst.py --force      # skip throttle, always send
  python ai_analyst.py --status     # print current alert state
  python ai_analyst.py --dry-run    # analyze but don't send Telegram
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("[ERROR] anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

# ── UTF-8 fix for Windows console ─────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE             = Path(__file__).resolve().parent
ENV_PATH         = HERE.parent.parent.parent / ".env.local"
PORTFOLIO_FILE   = HERE / "kraken_portfolio.json"
ALERT_STATE_FILE = HERE / ".alert-state.json"

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ALERT_URGENCY_THRESHOLD = 7   # only send if >= this
MAX_ALERTS_PER_DAY      = 3   # daily cap
MIN_HOURS_BETWEEN       = 2   # minimum gap between alerts


# ── Env loading ────────────────────────────────────────────────────────────────
def load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
ANTHROPIC_KEY   = ENV.get("ANTHROPIC_API_KEY", "")
TELEGRAM_TOKEN  = ENV.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT   = ENV.get("TELEGRAM_CHAT_ID", "")


# ── Alert state management ─────────────────────────────────────────────────────
def load_alert_state() -> dict:
    default = {
        "last_ai_alert_utc": None,
        "last_alert_urgency": 0,
        "alert_count_today": 0,
        "last_count_date": None,
    }
    if ALERT_STATE_FILE.exists():
        try:
            return {**default, **json.loads(ALERT_STATE_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return default


def save_alert_state(state: dict):
    ALERT_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _is_throttled() -> tuple[bool, str]:
    """Returns (is_throttled, reason)."""
    state = load_alert_state()
    now   = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    # Reset daily count if new day
    if state["last_count_date"] != today:
        state["alert_count_today"] = 0
        state["last_count_date"]   = today
        save_alert_state(state)

    if state["alert_count_today"] >= MAX_ALERTS_PER_DAY:
        return True, f"Daily cap reached ({MAX_ALERTS_PER_DAY} alerts/day)"

    if state["last_ai_alert_utc"]:
        try:
            last = datetime.fromisoformat(state["last_ai_alert_utc"].replace("Z", "+00:00"))
            hours_since = (now - last).total_seconds() / 3600
            if hours_since < MIN_HOURS_BETWEEN:
                return True, f"Too soon ({hours_since:.1f}h since last alert, min {MIN_HOURS_BETWEEN}h)"
        except Exception:
            pass

    return False, ""


def _update_alert_state(urgency: int):
    state = load_alert_state()
    now   = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    if state["last_count_date"] != today:
        state["alert_count_today"] = 0
        state["last_count_date"]   = today

    state["last_ai_alert_utc"]  = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    state["last_alert_urgency"] = urgency
    state["alert_count_today"]  += 1
    save_alert_state(state)


# ── Portfolio context builder ──────────────────────────────────────────────────
def _build_context(portfolio_data: dict) -> str:
    """Build compact text summary for Claude to analyze."""
    p = portfolio_data.get("portfolio", {})
    lines = [
        f"Generated: {portfolio_data.get('generated_at', 'unknown')}",
        f"Total USD: ${p.get('total_usd', 0):,.2f}",
        "",
        "HOLDINGS:",
    ]

    for b in p.get("balances", []):
        if b.get("is_stablecoin"):
            continue
        sym   = b.get("symbol", b["asset"])
        qty   = b["qty"]
        val   = b["usd_value"]
        pnl   = b.get("pnl_pct")
        ch24  = b.get("change_24h_pct")
        pnl_s = f" P&L:{'+' if pnl >= 0 else ''}{pnl:.1f}%" if pnl is not None else ""
        ch_s  = f" 24h:{'+' if ch24 >= 0 else ''}{ch24:.1f}%" if ch24 is not None else ""
        lines.append(f"  {sym}: {qty:.6f} = ${val:,.2f}{pnl_s}{ch_s}")

    if p.get("stablecoins_usd", 0) > 0:
        lines.append(f"  USD (stable): ${p['stablecoins_usd']:,.2f}")

    open_orders = p.get("open_orders", [])
    if open_orders:
        lines.append(f"\nOPEN ORDERS ({len(open_orders)}):")
        for o in open_orders[:3]:
            lines.append(f"  {o['type'].upper()} {o['pair']} @ ${o['price']:,.4f}  age:{o['age_hours']:.0f}h")

    recent = p.get("recent_trades", [])
    if recent:
        last = recent[0]
        lines.append(f"\nLAST TRADE: {last['type'].upper()} {last['pair']} @ ${last['price_executed']:,.2f}  {last['closed_at'][:10]}")

    return "\n".join(lines)


# ── Claude Haiku analysis ──────────────────────────────────────────────────────
def analyze_portfolio(portfolio_data: dict) -> dict:
    """
    Analyze portfolio with Claude Haiku. Returns urgency score + summary.
    Returns: {"urgency": int, "summary": str, "action": str|None, "raw": str}
    """
    if not ANTHROPIC_KEY:
        print("[AI Analyst] ANTHROPIC_API_KEY not set — skipping analysis")
        return {"urgency": 0, "summary": "API key not configured", "action": None, "raw": ""}

    context = _build_context(portfolio_data)

    system_prompt = (
        "You are a crypto portfolio intelligence analyst for a personal investor (Shami). "
        "Be concise and factual. Only flag genuine, actionable signals — avoid crying wolf. "
        "The investor is in Aruba (AST), budget-conscious, systems thinker. "
        "Holdings are BTC, ETH, SOL, OPN, EIGEN, PENGU, BABY (all Kraken). "
        "Average buy prices are: BTC $90,111 | ETH $3,151 | SOL $151 | OPN $0.33 | EIGEN $0.30 | BABY $0.028."
    )

    user_prompt = (
        f"Analyze this portfolio snapshot and provide:\n"
        f"1. URGENCY_SCORE: integer 1-10 (1=nothing notable, 10=act immediately)\n"
        f"2. SUMMARY: 2-3 sentences. What's notable? Any red flags or opportunities?\n"
        f"3. ACTION: One specific actionable sentence, or 'none' if nothing urgent.\n\n"
        f"Format your response EXACTLY as:\n"
        f"URGENCY_SCORE: [number]\n"
        f"SUMMARY: [text]\n"
        f"ACTION: [text or none]\n\n"
        f"Portfolio data:\n{context}"
    )

    try:
        client   = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text.strip()
        return _parse_analysis(raw)
    except Exception as e:
        print(f"[AI Analyst] Claude API error: {e}")
        return {"urgency": 0, "summary": f"Analysis failed: {e}", "action": None, "raw": ""}


def _parse_analysis(raw: str) -> dict:
    """Parse Claude's structured response."""
    urgency = 0
    summary = ""
    action  = None

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("URGENCY_SCORE:"):
            try:
                urgency = int(line.split(":", 1)[1].strip())
                urgency = max(1, min(10, urgency))
            except ValueError:
                pass
        elif line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
        elif line.startswith("ACTION:"):
            action_text = line.split(":", 1)[1].strip()
            action = None if action_text.lower() in ("none", "n/a", "") else action_text

    return {"urgency": urgency, "summary": summary, "action": action, "raw": raw}


# ── Telegram alert ─────────────────────────────────────────────────────────────
def _send_telegram_alert(urgency: int, summary: str, action: str | None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("[Telegram] Not configured — alert not sent")
        return

    if urgency >= 9:
        prefix = "🚨 <b>URGENT SIGNAL</b>"
    elif urgency >= 7:
        prefix = "⚠️ <b>MARKET SIGNAL</b>"
    else:
        prefix = "📊 <b>Portfolio Note</b>"

    lines = [
        f"{prefix} [{urgency}/10]",
        "",
        summary,
    ]
    if action:
        lines += ["", f"💡 <b>Action:</b> {action}"]
    lines += ["", "/portfolio for full view"]

    msg = "\n".join(lines)
    if len(msg) > 4000:
        msg = msg[:3990] + "\n..."

    try:
        payload = json.dumps({
            "chat_id":    TELEGRAM_CHAT,
            "text":       msg,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        print(f"[Telegram] ✓ Alert sent (urgency {urgency}/10)")
    except Exception as e:
        print(f"[Telegram] Failed: {e}")


# ── Main public function (importable) ─────────────────────────────────────────
def analyze_and_alert(portfolio_data: dict, force: bool = False, dry_run: bool = False) -> dict:
    """
    Analyze portfolio. Send Telegram alert if urgency >= 7 and not throttled.
    Returns the analysis dict.
    Importable by portfolio_monitor.py and morning-briefing.py.
    """
    print(f"\n[AI Analyst] Analyzing portfolio...", end=" ", flush=True)
    result = analyze_portfolio(portfolio_data)
    urgency = result["urgency"]
    print(f"Urgency: {urgency}/10")

    if urgency > 0:
        print(f"[AI Analyst] {result['summary']}")
        if result["action"]:
            print(f"[AI Analyst] Action: {result['action']}")

    should_alert = urgency >= ALERT_URGENCY_THRESHOLD

    if should_alert and not force:
        throttled, reason = _is_throttled()
        if throttled:
            print(f"[AI Analyst] Alert suppressed — {reason}")
            should_alert = False

    if should_alert:
        if dry_run:
            print(f"[AI Analyst] DRY RUN — would send alert (urgency {urgency}/10)")
        else:
            _send_telegram_alert(urgency, result["summary"], result["action"])
            _update_alert_state(urgency)
    elif urgency < ALERT_URGENCY_THRESHOLD:
        print(f"[AI Analyst] No alert — urgency {urgency} below threshold {ALERT_URGENCY_THRESHOLD}")

    return result


def print_status():
    """Print current alert state to console."""
    state = load_alert_state()
    now   = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    print(f"\n{SEP}")
    print(f"  AI Analyst Alert State")
    print(SEP)
    print(f"  Threshold:   {ALERT_URGENCY_THRESHOLD}/10")
    print(f"  Daily cap:   {MAX_ALERTS_PER_DAY} alerts/day")
    print(f"  Min gap:     {MIN_HOURS_BETWEEN}h between alerts")
    print()

    count_today = state["alert_count_today"] if state["last_count_date"] == today else 0
    print(f"  Today's alerts:  {count_today}/{MAX_ALERTS_PER_DAY}")
    print(f"  Last urgency:    {state['last_alert_urgency']}/10")

    if state["last_ai_alert_utc"]:
        last = datetime.fromisoformat(state["last_ai_alert_utc"].replace("Z", "+00:00"))
        hours_since = (now - last).total_seconds() / 3600
        print(f"  Last alert:      {state['last_ai_alert_utc']}  ({hours_since:.1f}h ago)")
        if hours_since < MIN_HOURS_BETWEEN:
            remaining = MIN_HOURS_BETWEEN - hours_since
            print(f"  Next alert:      in {remaining:.1f}h (throttled)")
        else:
            print(f"  Next alert:      READY")
    else:
        print(f"  Last alert:      never")
        print(f"  Next alert:      READY")
    print(SEP)


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="YNAI5 AI Portfolio Analyst")
    parser.add_argument("--force",   action="store_true", help="Skip throttle, always send alert")
    parser.add_argument("--dry-run", action="store_true", help="Analyze but don't send Telegram")
    parser.add_argument("--status",  action="store_true", help="Print alert state")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if not PORTFOLIO_FILE.exists():
        print(f"[ERROR] Portfolio file not found: {PORTFOLIO_FILE}")
        print("        Run portfolio_monitor.py first.")
        sys.exit(1)

    portfolio_data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    analyze_and_alert(portfolio_data, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
