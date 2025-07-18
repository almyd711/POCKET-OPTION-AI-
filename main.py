import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime
import random

# ✅ توكن البوت
TOKEN = "8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U"

# ✅ الأزواج المتاحة
PAIRS = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC"]

# ✅ محاكاة بيانات السوق
def get_market_data():
    ema20 = round(random.uniform(1.080, 1.090), 4)
    ema50 = round(random.uniform(1.078, 1.088), 4)
    rsi = round(random.uniform(30, 70), 2)
    bollinger_position = random.choice(["فوق الحد العلوي", "عند الحد الأوسط", "أسفل الحد السفلي"])
    direction = "صاعد ✅" if ema20 > ema50 else "هابط 🔻"
    recommendation = "شراء (CALL)" if ema20 > ema50 and rsi < 70 else "بيع (PUT)"
    arrow = "⬆️" if "شراء" in recommendation else "⬇️"
    return ema20, ema50, rsi, bollinger_position, direction, recommendation, arrow

# ✅ توليد رسالة التوصية
def generate_signal(pair):
    ema20, ema50, rsi, boll_pos, trend, reco, arrow = get_market_data()
    now = datetime.now().strftime("%I:%M %p")
    message = f"""📊 التوصية: {reco}
💱 الـزوج: [{pair}] 
🔍 التحليل:
🔹 EMA:
- EMA20 = {ema20}
- EMA50 = {ema50}
📈 الاتجاه: {trend}

🔸 RSI = {rsi}
{"✅ منطقة تداول طبيعية" if 30 < rsi < 70 else "⚠️ تشبع سوقي"}

🔻 Bollinger Bands: {boll_pos}

📚 شرح المؤشرات:
- EMA20 {'>' if ema20 > ema50 else '<'} EMA50 → {"صعود" if ema20 > ema50 else "هبوط"}
- RSI {"< 70" if rsi < 70 else "> 70"} → {"غير مشبع" if rsi < 70 else "تشبّع شرائي"}
- Bollinger → يعطي احتمالات الانعكاس
🤔: {arrow}
⏱️ الفريم: 1 دقيقة
⏰ التوقيت: {now}
"""
    return message

# ✅ بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[pair] for pair in PAIRS]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("اختر الزوج الذي تريد التوصيات عليه:", reply_markup=reply_markup)

# ✅ إرسال التوصية عند اختيار الزوج
async def handle_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = update.message.text.strip()
    if pair in PAIRS:
        signal = generate_signal(pair)
        await update.message.reply_text(signal)
    else:
        await update.message.reply_text("❌ الزوج غير معروف. الرجاء اختيار زوج من القائمة.")

# ✅ إعداد البوت
def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pair))
    app.run_polling()

if __name__ == "__main__":
    main()
lling()

if __name__ == "__main__":
    main()
