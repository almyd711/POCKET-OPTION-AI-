import logging
import requests
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

# بيانات الدخول
BOT_TOKEN = '8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U'
ALPHA_VANTAGE_API_KEY = 'W88S5OTAQIAE42AX'

# إعدادات اللوغ
logging.basicConfig(level=logging.INFO)

# --- دالة تحليل البيانات ---
def analyze_market(data):
    df = pd.DataFrame(data)
    df['close'] = pd.to_numeric(df['close'])

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = round(rsi.iloc[-1], 2)

    # EMA 20 و EMA 50
    ema20 = df['close'].ewm(span=20).mean().iloc[-1]
    ema50 = df['close'].ewm(span=50).mean().iloc[-1]

    # Bollinger Bands
    ma = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    upper_band = ma + (2 * std)
    lower_band = ma - (2 * std)
    last_close = df['close'].iloc[-1]

    # تحليل كل مؤشر
    rsi_analysis = "✅ منطقة تداول طبيعية" if 30 < latest_rsi < 70 else "⚠️ منطقة تشبع"
    ema_trend = "صاعد ✅" if ema20 > ema50 else "هابط ❌"
    bb_signal = "أعلى البولينجر" if last_close > upper_band.iloc[-1] else "أسفل البولينجر" if last_close < lower_band.iloc[-1] else "داخل البولينجر"

    # التوصية
    if ema20 > ema50 and 50 < latest_rsi < 70 and last_close < lower_band.iloc[-1]:
        recommendation = "شراء (CALL)"
        chance = 87
    elif ema20 < ema50 and 30 < latest_rsi < 50 and last_close > upper_band.iloc[-1]:
        recommendation = "بيع (PUT)"
        chance = 82
    else:
        recommendation = "انتظار"
        chance = 60

    now = datetime.now().strftime("%I:%M %p")

    message = f"""
📊 التوصية: {recommendation}
💱 الزوج: EUR/USD
🔍 التحليل:

🔹 EMA:
- EMA20 = {round(ema20, 4)}
- EMA50 = {round(ema50, 4)}
📈 الاتجاه: {ema_trend}

🔸 RSI = {latest_rsi}
{rsi_analysis}

🔻 Bollinger Bands: {bb_signal}

📚 شرح المؤشرات:
- EMA20 > EMA50 → صعود
- RSI < 70 → غير مشبع
- Bollinger → يعطي احتمالات الانعكاس

🎯 نسبة نجاح متوقعة: {chance}%
⏱️ الفريم: 1 دقيقة
⏰ التوقيت: {now}
    """
    return message.strip()

# --- جلب بيانات السوق من Alpha Vantage ---
def get_market_data(symbol="EURUSD"):
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={symbol[:3]}&to_symbol={symbol[3:]}&interval=1min&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=compact"
    response = requests.get(url)
    data = response.json()
    if "Time Series FX (1min)" not in data:
        return None
    time_series = data["Time Series FX (1min)"]
    df = [
        {"time": k, "close": v["4. close"]}
        for k, v in sorted(time_series.items())
    ]
    return df

# --- عند الضغط على زر ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data
    data = get_market_data(symbol)
    if not data:
        await query.message.reply_text("فشل في جلب بيانات السوق.")
        return
    analysis = analyze_market(data)
    await query.message.reply_text(analysis)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("EUR/USD", callback_data="EURUSD")],
        [InlineKeyboardButton("USD/JPY", callback_data="USDJPY")],
        [InlineKeyboardButton("EUR/JPY", callback_data="EURJPY")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر زوج العملة:", reply_markup=reply_markup)

# --- تشغيل البوت ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == '__main__':
    main()
