import logging
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from telegram import Update, Bot
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask, request
import threading
import asyncio
import datetime
import os

TOKEN = os.environ.get("7870514226:AAGsJaD2jqxZJS7PjCoBV-WV6CdmSMBlQns")
APP_URL = os.environ.get("https://crypto-signal-bot-6-95qc.onrender.com")

bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# ====== نمونه دستور /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات با webhook فعاله ✅")

application.add_handler(CommandHandler("start", start))

# ====== Flask برای دریافت پیام‌های تلگرام ======
flask_app = Flask(__name__)

@flask_app.post(f"/{TOKEN}")
async def webhook_handler():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

# ====== راه‌اندازی webhook وقتی اپ اجرا میشه ======
async def set_webhook():
    await bot.set_webhook(url=f"{APP_URL}/{TOKEN}")
    
# ====== فقط برای نگه داشتن سرور Flask بخش ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ====== اجرای Flask در یک Thread جدا ======
threading.Thread(target=run_flask).start()

# ====== تنظیمات اصلی ======
BOT_TOKEN = "7870514226:AAGsJaD2jqxZJS7PjCoBV-WV6CdmSMBlQns"
AUTHORIZED_USER_ID = 342762208

# ====== تابع گرفتن قیمت و تحلیل RSI ======
def get_signal(coin_id="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
    res = requests.get(url)
    if res.status_code != 200:
        return "❌ خطا در دریافت داده از CoinGecko"

    prices = [price[1] for price in res.json()["prices"]]
    df = pd.DataFrame(prices, columns=["close"])
    rsi = RSIIndicator(df["close"]).rsi().iloc[-1]

    if rsi < 30:
        return f"🟢 سیگنال خرید برای {coin_id.upper()} (RSI={rsi:.2f})"
    elif rsi > 70:
        return f"🔴 سیگنال فروش برای {coin_id.upper()} (RSI={rsi:.2f})"
    else:
        return f"⚪️ فعلاً سیگنال مشخصی برای {coin_id.upper()} وجود ندارد (RSI={rsi:.2f})"

# ====== هندلر فرمان /start ======
async def start(update, context):
    await update.message.reply_text("👋 سلام! من ربات سیگنال‌دهنده ارز دیجیتال هستم. دستور /signal BTC رو امتحان کن!")

# ====== هندلر فرمان /signal ======
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    try:
        coin = context.args[0].lower()
    except:
        coin = "bitcoin"
    msg = get_signal(coin)
    await update.message.reply_text(msg)

# ====== تابع ارسال روزانه ======
async def daily_signal_task(app):
    while True:
        now = datetime.datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > target:
            target += datetime.timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        coins = ["bitcoin", "ethereum", "dogecoin", "shiba-inu"]
        for coin in coins:
            msg = get_signal(coin)
            await app.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=msg)

# ====== اجرای برنامه ======
async def main():
    app = ApplicationBuilder().token("7870514226:AAGsJaD2jqxZJS7PjCoBV-WV6CdmSMBlQns").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()
    
    asyncio.create_task(daily_signal_task(app))
    print("🤖 ربات راه‌اندازی شد")

if __name__ == "__main__":
    import asyncio
    asyncio.run(set_webhook())  # تنظیم webhook هنگام اجرای برنامه
    PORT = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=PORT)
