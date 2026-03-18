#!/usr/bin/env python3
"""
YNAI5 Prediction Tracker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feedback loop engine — logs Claude's market predictions,
scores outcomes after the timeframe expires, tracks accuracy.

Usage:
  python prediction_tracker.py --log BTC up 90000 72 0.7 "RSI oversold"
  python prediction_tracker.py --score        # score all due predictions
  python prediction_tracker.py --stats        # print performance summary
  python prediction_tracker.py --list         # list all predictions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── UTF-8 fix for Windows console ─────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE             = Path(__file__).resolve().parent
ENV_PATH         = HERE.parent.parent.parent / ".env.local"
PREDICTIONS_FILE = HERE / "predictions.json"
PERFORMANCE_FILE = HERE / "performance.json"

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Ticker → CoinGecko ID mapping
TICKER_TO_CG = {
    "BTC":   "bitcoin",
    "ETH":   "ethereum",
    "SOL":   "solana",
    "OPN":   "opinion",
    "EIGEN": "eigenlayer",
    "PENGU": "pudgy-penguins",
    "BCH":   "bitcoin-cash",
    "BABY":  "babylon",
}


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
COINGECKO_KEY = ENV.get("COINGECKO_API_KEY", "")


# ── File I/O ───────────────────────────────────────────────────────────────────
def load_predictions() -> dict:
    if PREDICTIONS_FILE.exists():
        try:
            return json.loads(PREDICTIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"predictions": []}


def save_predictions(data: dict):
    PREDICTIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_performance() -> dict:
    if PERFORMANCE_FILE.exists():
        try:
            return json.loads(PERFORMANCE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_updated": "",
        "overall": {"total": 0, "correct": 0, "incorrect": 0, "pending": 0, "accuracy_pct": 0.0},
        "by_ticker": {},
        "by_confidence": {
            "high_0.7+":      {"total": 0, "correct": 0, "accuracy_pct": 0.0},
            "medium_0.5-0.7": {"total": 0, "correct": 0, "accuracy_pct": 0.0},
            "low_under_0.5":  {"total": 0, "correct": 0, "accuracy_pct": 0.0},
        },
        "by_timeframe": {},
        "streak": {"current_correct": 0, "best_correct": 0},
    }


def save_performance(data: dict):
    PERFORMANCE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── CoinGecko price fetch ──────────────────────────────────────────────────────
def fetch_price(coingecko_id: str) -> float | None:
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coingecko_id}&vs_currencies=usd"
    )
    headers = {"Accept": "application/json", "User-Agent": "YNAI5-PredictionTracker/1.0"}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data.get(coingecko_id, {}).get("usd")
    except Exception as e:
        print(f"[CoinGecko] Error fetching {coingecko_id}: {e}")
        return None


# ── Core operations ────────────────────────────────────────────────────────────
def log_prediction(ticker: str, direction: str, target_price: float,
                   timeframe_hours: int, confidence: float, reasoning: str) -> str:
    """Log a new market prediction. Returns the prediction ID."""
    ticker    = ticker.upper()
    direction = direction.lower()

    if direction not in ("up", "down"):
        print("[ERROR] direction must be 'up' or 'down'")
        sys.exit(1)
    if not 0.0 <= confidence <= 1.0:
        print("[ERROR] confidence must be between 0.0 and 1.0")
        sys.exit(1)

    cg_id = TICKER_TO_CG.get(ticker)
    if not cg_id:
        print(f"[WARNING] Unknown ticker '{ticker}' — no CoinGecko mapping. Add it to TICKER_TO_CG.")

    now_utc  = datetime.now(timezone.utc)
    check_at = now_utc + timedelta(hours=timeframe_hours)
    pred_id  = f"pred_{now_utc.strftime('%Y%m%d_%H%M%S')}_{ticker}"

    # Fetch current price
    current_price = None
    if cg_id:
        print(f"[CoinGecko] Fetching current {ticker} price...", end=" ", flush=True)
        current_price = fetch_price(cg_id)
        print(f"${current_price:,.4f}" if current_price else "N/A")

    prediction = {
        "id":                 pred_id,
        "ticker":             ticker,
        "coingecko_id":       cg_id,
        "direction":          direction,
        "price_at_prediction": current_price,
        "target_price":       target_price,
        "has_target":         target_price > 0,
        "timeframe_hours":    timeframe_hours,
        "confidence":         confidence,
        "reasoning":          reasoning,
        "created_at":         now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check_at":           check_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status":             "pending",
        "outcome":            None,
        "price_at_outcome":   None,
        "outcome_pct":        None,
        "scored_at":          None,
    }

    data = load_predictions()
    data["predictions"].append(prediction)
    save_predictions(data)

    print(f"\n[Logged] {pred_id}")
    print(f"  {ticker} → {direction.upper()}  target: ${target_price:,.4f}  in {timeframe_hours}h")
    print(f"  Confidence: {confidence:.0%}  |  Check at: {check_at.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Reasoning: {reasoning}")
    return pred_id


def score_due_predictions() -> int:
    """Score all predictions where check_at has passed. Returns count scored."""
    data   = load_predictions()
    now    = datetime.now(timezone.utc)
    scored = 0

    for p in data["predictions"]:
        if p["status"] != "pending":
            continue

        check_at = datetime.fromisoformat(p["check_at"].replace("Z", "+00:00"))
        if now < check_at:
            continue

        # Due — fetch current price
        cg_id = p.get("coingecko_id")
        if not cg_id:
            print(f"[Skip] {p['id']} — no CoinGecko ID to score")
            continue

        print(f"[Scoring] {p['id']} ({p['ticker']} {p['direction'].upper()})...", end=" ", flush=True)
        current_price = fetch_price(cg_id)
        if current_price is None:
            print("price fetch failed — retry next run")
            continue

        base_price = p.get("price_at_prediction") or 0
        outcome_pct = ((current_price - base_price) / base_price * 100) if base_price else None

        # Determine correctness
        if p["direction"] == "up":
            correct = current_price > base_price
        else:
            correct = current_price < base_price

        # If prediction had a target price, check if it was reached
        if p.get("has_target") and p.get("target_price", 0) > 0:
            target = p["target_price"]
            if p["direction"] == "up":
                correct = current_price >= target
            else:
                correct = current_price <= target

        p["status"]           = "scored"
        p["outcome"]          = "correct" if correct else "incorrect"
        p["price_at_outcome"] = current_price
        p["outcome_pct"]      = round(outcome_pct, 2) if outcome_pct is not None else None
        p["scored_at"]        = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        result_icon = "✅" if correct else "❌"
        print(f"{result_icon} {p['outcome'].upper()}  |  ${base_price:,.4f} → ${current_price:,.4f}  ({'+' if outcome_pct >= 0 else ''}{outcome_pct:.1f}%)")
        scored += 1

    if scored > 0:
        save_predictions(data)
        _rebuild_performance(data)
        print(f"\n[Done] Scored {scored} prediction(s). Performance updated.")
    else:
        print("[Score] No predictions due for scoring.")

    return scored


def _rebuild_performance(data: dict):
    """Rebuild performance.json from all scored predictions."""
    scored = [p for p in data["predictions"] if p["status"] == "scored"]
    pending = [p for p in data["predictions"] if p["status"] == "pending"]

    total   = len(scored)
    correct = sum(1 for p in scored if p["outcome"] == "correct")
    incorrect = total - correct
    acc = round(correct / total * 100, 1) if total > 0 else 0.0

    # By ticker
    by_ticker = {}
    for p in scored:
        t = p["ticker"]
        if t not in by_ticker:
            by_ticker[t] = {"total": 0, "correct": 0, "accuracy_pct": 0.0}
        by_ticker[t]["total"] += 1
        if p["outcome"] == "correct":
            by_ticker[t]["correct"] += 1
    for t in by_ticker:
        n = by_ticker[t]["total"]
        c = by_ticker[t]["correct"]
        by_ticker[t]["accuracy_pct"] = round(c / n * 100, 1) if n > 0 else 0.0

    # By confidence bucket
    buckets = {
        "high_0.7+":      [p for p in scored if p.get("confidence", 0) >= 0.7],
        "medium_0.5-0.7": [p for p in scored if 0.5 <= p.get("confidence", 0) < 0.7],
        "low_under_0.5":  [p for p in scored if p.get("confidence", 0) < 0.5],
    }
    by_conf = {}
    for key, preds in buckets.items():
        n = len(preds)
        c = sum(1 for p in preds if p["outcome"] == "correct")
        by_conf[key] = {"total": n, "correct": c, "accuracy_pct": round(c / n * 100, 1) if n > 0 else 0.0}

    # By timeframe bucket
    by_tf = {}
    for p in scored:
        h = p.get("timeframe_hours", 0)
        if h <= 24:       bucket = "<=24h"
        elif h <= 72:     bucket = "25-72h"
        elif h <= 168:    bucket = "73-168h"
        else:             bucket = "168h+"
        if bucket not in by_tf:
            by_tf[bucket] = {"total": 0, "correct": 0, "accuracy_pct": 0.0}
        by_tf[bucket]["total"] += 1
        if p["outcome"] == "correct":
            by_tf[bucket]["correct"] += 1
    for b in by_tf:
        n = by_tf[b]["total"]
        c = by_tf[b]["correct"]
        by_tf[b]["accuracy_pct"] = round(c / n * 100, 1) if n > 0 else 0.0

    # Streak (from most recent scored first)
    recent = sorted(scored, key=lambda x: x.get("scored_at", ""), reverse=True)
    current_streak = 0
    for p in recent:
        if p["outcome"] == "correct":
            current_streak += 1
        else:
            break

    old_perf = load_performance()
    best_streak = max(old_perf.get("streak", {}).get("best_correct", 0), current_streak)

    perf = {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall": {
            "total":         total,
            "correct":       correct,
            "incorrect":     incorrect,
            "pending":       len(pending),
            "accuracy_pct":  acc,
        },
        "by_ticker":      by_ticker,
        "by_confidence":  by_conf,
        "by_timeframe":   by_tf,
        "streak": {
            "current_correct": current_streak,
            "best_correct":    best_streak,
        },
    }
    save_performance(perf)


def print_stats():
    """Print performance summary to console."""
    if not PERFORMANCE_FILE.exists():
        print("No performance data yet. Log and score some predictions first.")
        return

    p = load_performance()
    ov = p["overall"]

    print(f"\n{SEP}")
    print(f"  Prediction Performance")
    print(f"{SEP}")
    print(f"  Overall:    {ov['correct']}/{ov['total']} correct  ({ov['accuracy_pct']:.1f}%)")
    print(f"  Pending:    {ov['pending']}")
    print(f"  Streak:     {p['streak']['current_correct']} in a row  (best: {p['streak']['best_correct']})")

    print(f"\n  By Ticker:")
    for ticker, stats in sorted(p["by_ticker"].items(), key=lambda x: -x[1]["accuracy_pct"]):
        bar = "█" * int(stats["accuracy_pct"] / 10)
        print(f"    {ticker:<8} {stats['correct']}/{stats['total']}  {stats['accuracy_pct']:>5.1f}%  {bar}")

    print(f"\n  By Confidence:")
    for bucket, stats in p["by_confidence"].items():
        if stats["total"] > 0:
            print(f"    {bucket:<20} {stats['correct']}/{stats['total']}  {stats['accuracy_pct']:>5.1f}%")

    print(f"\n  By Timeframe:")
    for bucket, stats in sorted(p["by_timeframe"].items()):
        if stats["total"] > 0:
            print(f"    {bucket:<12} {stats['correct']}/{stats['total']}  {stats['accuracy_pct']:>5.1f}%")

    print(f"\n  Last updated: {p['last_updated']}")
    print(SEP)


def list_predictions(status_filter: str = None):
    """List all predictions, optionally filtered by status."""
    data = load_predictions()
    preds = data["predictions"]
    if status_filter:
        preds = [p for p in preds if p["status"] == status_filter]

    if not preds:
        print(f"No predictions{' with status ' + status_filter if status_filter else ''}.")
        return

    print(f"\n{SEP}")
    print(f"  Predictions ({len(preds)} total)")
    print(SEP)

    for p in sorted(preds, key=lambda x: x["created_at"], reverse=True):
        icon = {"pending": "⏳", "scored": "✅" if p.get("outcome") == "correct" else "❌"}.get(p["status"], "?")
        price_s = f"${p.get('price_at_prediction', 0):,.4f}" if p.get("price_at_prediction") else "N/A"
        outcome_s = ""
        if p["status"] == "scored":
            outcome_pct = p.get("outcome_pct", 0)
            outcome_s = f"  |  outcome: {'+' if outcome_pct >= 0 else ''}{outcome_pct:.1f}%"
        print(f"  {icon} [{p['created_at'][:10]}] {p['ticker']} {p['direction'].upper():<5} "
              f"conf:{p['confidence']:.0%}  {price_s} → ${p.get('target_price', 0):,.4f}  "
              f"({p['timeframe_hours']}h){outcome_s}")
        print(f"       {p['reasoning'][:80]}")

    print(SEP)


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="YNAI5 Prediction Tracker")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--log",    nargs=6, metavar=("TICKER", "DIRECTION", "TARGET", "HOURS", "CONFIDENCE", "REASONING"),
                       help="Log prediction: --log BTC up 90000 72 0.7 'reasoning'")
    group.add_argument("--score",  action="store_true", help="Score all due predictions")
    group.add_argument("--stats",  action="store_true", help="Print performance summary")
    group.add_argument("--list",   nargs="?", const="all", metavar="STATUS",
                       help="List predictions (optionally filter by status: pending/scored)")

    args = parser.parse_args()

    if args.log:
        ticker, direction, target, hours, confidence, reasoning = args.log
        log_prediction(
            ticker=ticker,
            direction=direction,
            target_price=float(target),
            timeframe_hours=int(hours),
            confidence=float(confidence),
            reasoning=reasoning,
        )

    elif args.score:
        score_due_predictions()

    elif args.stats:
        print_stats()

    elif args.list:
        status = None if args.list == "all" else args.list
        list_predictions(status_filter=status)


if __name__ == "__main__":
    main()
