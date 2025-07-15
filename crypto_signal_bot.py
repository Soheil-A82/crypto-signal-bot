import logging
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import datetime

# ====== تنظیمات اصلی ======
BOT_TOKEN = "7870514226:AAGsJaD2jqxZJS7PjCoBV-WV6CdmSMBlQns"  # توکن ربات تلگرامت رو اینجا بذار
AUTHORIZED_USER_ID = 342762208  # فقط برای تو کار می‌کنه

# ====== تابع گرفتن قیمت و تحلیل RSI ======
def get_signal(coin_id="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
    res = requests.get(url)
    if res.status_code != 200:
        return "❌ خطا در دریافت داده از CoinGecko"

    prices = [price[1] for price in res.json()["prices"]]
    df = pd.DataFrame(prices, columns=["close"])

    rsi_indicator = RSIIndicator(close=df["close"])
    rsi = rsi_indicator.rsi().iloc[-1]

    if rsi < 30:
        return f"🟢 سیگنال خرید برای {coin_id.upper()} (RSI={rsi:.2f})"
    elif rsi > 70:
        return f"🔴 سیگنال فروش برای {coin_id.upper()} (RSI={rsi:.2f})"
    else:
        return f"⚪️ فعلاً سیگنال مشخصی برای {coin_id.upper()} وجود ندارد (RSI={rsi:.2f})"


# ====== هندلر فرمان /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
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
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))

    asyncio.create_task(daily_signal_task(app))

    print("🤖 ربات راه‌اندازی شد")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
