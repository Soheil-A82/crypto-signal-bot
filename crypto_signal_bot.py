import logging
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request
import threading
import asyncio
import datetime
import os

# ====== دریافت توکن و آدرس اپ از محیط ======
TOKEN = os.environ.get("BOT_TOKEN")
APP_URL = os.environ.get("APP_URL")

bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# ====== تنظیم پورت ======
PORT = int(os.environ.get("PORT", 5000))

# ====== Flask برای دریافت پیام‌های تلگرام ======
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return "ok"

@flask_app.route('/')
def home():
    return "Bot is running"

# ====== تنظیمات اصلی ======
AUTHORIZED_USER_ID = 342762208

# ====== تابع گرفتن قیمت و تحلیل RSI ======
def get_signal(coin_id="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        return f"❌ خطا در دریافت داده از CoinGecko: {e}"

    prices = [price[1] for price in res.json().get("prices", [])]
    if not prices:
        return "❌ داده‌ای برای تحلیل دریافت نشد."

    df = pd.DataFrame(prices, columns=["close"])
    rsi = RSIIndicator(df["close"]).rsi().iloc[-1]

    if rsi < 30:
        return f"🟢 سیگنال خرید برای {coin_id.upper()} (RSI={rsi:.2f})"
    elif rsi > 70:
        return f"🔴 سیگنال فروش برای {coin_id.upper()} (RSI={rsi:.2f})"
    else:
        return f"⚪️ فعلاً سیگنال مشخصی برای {coin_id.upper()} وجود ندارد (RSI={rsi:.2f})"

# ====== هندلر فرمان /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 سلام! من ربات سیگنال‌دهنده ارز دیجیتال هستم. دستور /signal BTC رو امتحان کن!")

# ====== هندلر فرمان /signal ======
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    try:
        coin = context.args[0].lower()
    except IndexError:
        coin = "bitcoin"
    msg = get_signal(coin)
    await update.message.reply_text(msg)

# ====== تابع ارسال روزانه ======
async def daily_signal_task(telegram_app):
    while True:
        now = datetime.datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > target:
            target += datetime.timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        coins = ["bitcoin", "ethereum", "dogecoin", "shiba-inu"]
        for coin in coins:
            msg = get_signal(coin)
            await telegram_app.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=msg)

# ====== تنظیم webhook ======
async def set_webhook():
    await bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

# ====== اجرای برنامه ======
async def main():
    application.add_handler(CommandHandler("signal", signal))
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.start()

    asyncio.create_task(daily_signal_task(application))
    print("🤖 ربات راه‌اندازی شد")

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()

    async def runner():
        await set_webhook()
        await main()

    asyncio.run(runner())
