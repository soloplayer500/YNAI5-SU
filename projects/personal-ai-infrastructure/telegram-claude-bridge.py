"""
YNAI5 Telegram-Claude Bridge
Chat with Claude from phone via @SoloClaude5_bot
Reads TELEGRAM_BOT_TOKEN + ANTHROPIC_API_KEY from .env.local

Portfolio commands (reads kraken_portfolio.json committed by GitHub Actions):
  /portfolio  — full portfolio summary
  /positions  — balances only
  /orders     — open orders only
"""
import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

env_path = Path(__file__).parent.parent.parent / ".env.local"
load_dotenv(env_path, override=True)

PORTFOLIO_JSON   = Path(__file__).parent.parent / "crypto-monitoring" / "kraken" / "kraken_portfolio.json"
SESSION_LOG_DIR  = Path(__file__).parent.parent / "crypto-monitoring" / "telegram-sessions"
MEMORY_FILE      = Path(__file__).parent.parent.parent / "memory" / "MEMORY.md"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

if not TELEGRAM_BOT_TOKEN or not ANTHROPIC_API_KEY:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or ANTHROPIC_API_KEY in .env.local")

client = Anthropic(api_key=ANTHROPIC_API_KEY)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

SYSTEM_PROMPT = """You are Ryn, Shami's personal AI assistant on his YNAI5-SU laptop (24/7).

ABOUT SHAMI: AI Systems Builder in Aruba. Systems thinker, MVP first, infrastructure mindset.
TOP PRIORITY: AI social media automation pipeline (TikTok/YouTube/Instagram) for revenue.
ALSO ACTIVE: Crypto monitoring (Kraken + Revolut), YNAI5 music channel (waiting on Distrokid).
HARDWARE: HP Laptop 15, 8GB RAM, AMD Ryzen 5, integrated GPU -- budget-sensitive.

RESPONSE STYLE: Professional but friendly, no filler, high signal, structured headings.
On phone: keep responses concise. Actionable steps. Challenge weak reasoning. MVP first."""

conversation_history = {}
MAX_HISTORY = 20


# ── Session logger ─────────────────────────────────────────────────────────────
def _log_session(user_msg: str, assistant_reply: str):
    """Append each exchange to a daily session log file."""
    try:
        SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
        today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = SESSION_LOG_DIR / f"{today}.json"

        entry = {
            "ts":        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user":      user_msg[:500],
            "assistant": assistant_reply[:800],
        }

        data = {"sessions": []}
        if log_file.exists():
            try:
                data = json.loads(log_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        data["sessions"].append(entry)
        log_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logging.warning(f"Session log error: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Unauthorized.")
        return
    conversation_history[chat_id] = []
    await update.message.reply_text(
        "Ryn online. YNAI5 workspace connected.\n"
        "Commands: /clear /status /portfolio /positions /orders /memory"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    conversation_history[chat_id] = []
    await update.message.reply_text("Conversation cleared.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    h = len(conversation_history.get(chat_id, []))
    await update.message.reply_text(f"Bridge: ONLINE\nModel: claude-haiku-4-5\nHistory: {h} msgs")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        logging.warning(f"Blocked unauthorized: {chat_id}")
        return
    user_message = update.message.text
    if not user_message:
        return
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    conversation_history[chat_id].append({"role": "user", "content": user_message})
    if len(conversation_history[chat_id]) > MAX_HISTORY:
        conversation_history[chat_id] = conversation_history[chat_id][-MAX_HISTORY:]
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_history[chat_id]
        )
        reply = response.content[0].text
        conversation_history[chat_id].append({"role": "assistant", "content": reply})

        # Log exchange to daily session file
        _log_session(user_message, reply)

        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            chunks, current = [], ""
            for line in reply.split("\n"):
                if len(current) + len(line) + 1 > 4000:
                    chunks.append(current)
                    current = line
                else:
                    current = current + "\n" + line if current else line
            if current:
                chunks.append(current)
            for chunk in chunks:
                await update.message.reply_text(chunk)
    except Exception as e:
        logging.error(f"Claude API error: {e}")
        await update.message.reply_text(f"Error: {str(e)[:200]}")


# ── /memory command ────────────────────────────────────────────────────────────
async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save a note directly to MEMORY.md from Telegram."""
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return

    note = " ".join(context.args) if context.args else ""
    if not note:
        await update.message.reply_text(
            "Usage: /memory [your note]\n"
            "Example: /memory I prefer to buy SOL at dips below $130"
        )
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"\n- [{today}] {note}"

    try:
        with MEMORY_FILE.open("a", encoding="utf-8") as f:
            f.write(entry)
        await update.message.reply_text(f"✅ Saved to MEMORY.md:\n{note}")
        logging.info(f"Memory saved: {note[:80]}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save: {str(e)[:100]}")


# ── Portfolio helpers ──────────────────────────────────────────────────────────
def _load_portfolio_json():
    """Load kraken_portfolio.json. Returns (data, age_minutes) or (None, None)."""
    if not PORTFOLIO_JSON.exists():
        return None, None
    try:
        data = json.loads(PORTFOLIO_JSON.read_text(encoding="utf-8"))
        generated = data.get("generated_at", "")
        age_min = None
        if generated:
            dt = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            age_min = int((datetime.now(timezone.utc) - dt).total_seconds() / 60)
        return data, age_min
    except Exception as e:
        logging.error(f"Portfolio JSON read error: {e}")
        return None, None


def _age_warning(age_min: int | None) -> str:
    if age_min is not None and age_min > 35:
        return f"⚠️ Data from {age_min}min ago — sync pending\n\n"
    return ""


def _fmt_price(price: float) -> str:
    if price >= 1000:  return f"${price:,.0f}"
    if price >= 1:     return f"${price:,.2f}"
    if price >= 0.01:  return f"${price:.4f}"
    return f"${price:.6f}"


def _format_portfolio_summary(data: dict, age_min: int | None) -> str:
    p = data.get("portfolio", {})
    balances    = [b for b in p.get("balances", []) if not b.get("is_stablecoin")]
    stable_usd  = p.get("stablecoins_usd", 0)
    open_orders = p.get("open_orders", [])
    trades      = p.get("recent_trades", [])
    total       = p.get("total_usd", 0)

    lines = [_age_warning(age_min)]
    lines.append(f"📊 <b>Kraken Portfolio</b>")
    lines.append(f"💰 <b>Total: ${total:,.2f}</b>")
    if stable_usd > 0:
        lines.append(f"   Net crypto: ${total - stable_usd:,.2f}  |  Cash: ${stable_usd:,.2f}")
    lines.append("")

    for b in balances[:8]:
        sym   = b.get("symbol", b["asset"])
        qty   = b["qty"]
        val   = b["usd_value"]
        pnl   = b.get("pnl_pct")
        ch24  = b.get("change_24h_pct")
        pnl_s = f" [{'+' if pnl >= 0 else ''}{pnl:.0f}%]" if pnl is not None else ""
        ch_s  = f" {'+' if ch24 >= 0 else ''}{ch24:.1f}%24h" if ch24 is not None else ""
        qty_s = f"{qty:.6f}".rstrip("0").rstrip(".")
        lines.append(f"<code>{sym:<6} {qty_s:<14} {_fmt_price(val)}{pnl_s}{ch_s}</code>")

    if stable_usd > 0:
        lines.append(f"<code>{'USD':<6} {'(stable)':<14} ${stable_usd:,.2f}</code>")

    lines.append("")
    if open_orders:
        lines.append(f"📋 <b>{len(open_orders)} open order(s):</b>")
        for o in open_orders[:3]:
            lines.append(f"  {o['type'].upper()} {o['pair']} @ {_fmt_price(o['price'])}  ({o['age_hours']:.0f}h ago)")
    else:
        lines.append("📋 No open orders")

    if trades:
        last = trades[0]
        lines.append(f"🕐 Last: {last['type'].upper()} {last['pair']} @ {_fmt_price(last['price_executed'])}  {last['closed_at'][:10]}")

    lines.append(f"\n🕐 Data: {data.get('generated_at', '')[:16].replace('T', ' ')} UTC")
    msg = "\n".join(lines)
    return msg[:4000] + "\n..." if len(msg) > 4000 else msg


def _format_positions_only(data: dict, age_min: int | None) -> str:
    p        = data.get("portfolio", {})
    balances = [b for b in p.get("balances", []) if not b.get("is_stablecoin")]
    total    = p.get("total_usd", 0)

    lines = [_age_warning(age_min), f"💰 <b>Positions — ${total:,.2f} total</b>", ""]
    for b in balances:
        sym   = b.get("symbol", b["asset"])
        qty   = b["qty"]
        val   = b["usd_value"]
        price = b.get("price_usd", 0)
        pnl   = b.get("pnl_pct")
        pnl_s = f" [{'+' if pnl >= 0 else ''}{pnl:.0f}%]" if pnl is not None else ""
        qty_s = f"{qty:.6f}".rstrip("0").rstrip(".")
        lines.append(f"<code>{sym:<6} {qty_s:<14} {_fmt_price(val)}  @ {_fmt_price(price)}{pnl_s}</code>")
    return "\n".join(lines)


def _format_orders_only(data: dict, age_min: int | None) -> str:
    p           = data.get("portfolio", {})
    open_orders = p.get("open_orders", [])
    trades      = p.get("recent_trades", [])

    lines = [_age_warning(age_min)]
    if open_orders:
        lines.append(f"📋 <b>{len(open_orders)} open order(s):</b>")
        for o in open_orders:
            filled_pct = (o["volume_filled"] / o["volume"] * 100) if o["volume"] > 0 else 0
            lines.append(
                f"<code>{o['type'].upper():<5} {o['pair']:<10} "
                f"@ {_fmt_price(o['price'])}  vol:{o['volume']:.6f}  "
                f"filled:{filled_pct:.0f}%  age:{o['age_hours']:.1f}h</code>"
            )
    else:
        lines.append("📋 No open orders")
        if trades:
            last = trades[0]
            lines.append(f"\n🕐 Last trade: {last['type'].upper()} {last['pair']} "
                         f"@ {_fmt_price(last['price_executed'])}  {last['closed_at'][:10]}")

    if trades and open_orders:
        lines.append(f"\n<b>Recent trades:</b>")
        for t in trades[:5]:
            lines.append(f"<code>{t['type'].upper():<5} {t['pair']:<10} "
                         f"@ {_fmt_price(t['price_executed'])}  {t['closed_at'][:10]}</code>")
    return "\n".join(lines)


# ── Portfolio command handlers ─────────────────────────────────────────────────
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    data, age_min = _load_portfolio_json()
    if data is None:
        await update.message.reply_text(
            "Portfolio data not available yet.\n"
            "GitHub Actions syncs every 30min — or run portfolio_monitor.py locally."
        )
        return
    await update.message.reply_text(_format_portfolio_summary(data, age_min), parse_mode="HTML")


async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    data, age_min = _load_portfolio_json()
    if data is None:
        await update.message.reply_text("Portfolio data not available yet.")
        return
    await update.message.reply_text(_format_positions_only(data, age_min), parse_mode="HTML")


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    data, age_min = _load_portfolio_json()
    if data is None:
        await update.message.reply_text("Portfolio data not available yet.")
        return
    await update.message.reply_text(_format_orders_only(data, age_min), parse_mode="HTML")


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("positions", positions))
    app.add_handler(CommandHandler("orders", orders))
    app.add_handler(CommandHandler("memory", memory))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("YNAI5 Telegram-Claude Bridge starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
