"""
YNAI5 Telegram-Claude Bridge
Chat with Claude from phone via @SoloClaude5_bot
Reads TELEGRAM_BOT_TOKEN + ANTHROPIC_API_KEY from .env.local
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

env_path = Path(__file__).parent.parent.parent / ".env.local"
load_dotenv(env_path, override=True)

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Unauthorized.")
        return
    conversation_history[chat_id] = []
    await update.message.reply_text("Ryn online. YNAI5 workspace connected.\nCommands: /clear /status")


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


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("YNAI5 Telegram-Claude Bridge starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
