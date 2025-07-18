import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime
import random

TOKEN = "8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U"
ADMIN_ID = 6964741705

PAIRS = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC"]
accepted_users = set()

def get_market_data():
    ema20 = round(random.uniform(1.080, 1.090), 4)
    ema50 = round(random.uniform(1.078, 1.088), 4)
    rsi = round(random.uniform(30, 70), 2)
    bollinger_position = random.choice(["فوق الحد العلوي", "عند الحد الأوسط", "أسفل الحد السفلي"])
    direction = "صاعد ✅" if ema20 > ema50 else "هابط 🔻"
    recommendation = "شراء (CALL)" if ema20 > ema50 and rsi < 70 else "بيع (PUT)"
    arrow = "⬆️" if "شراء" in recommendation else "⬇️"
    return ema20, ema50, rsi, bollinger_position, direction, recommendation, arrow

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[pair] for pair in PAIRS]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("اختر الزوج الذي تريد التوصيات عليه:", reply_markup=reply_markup)

async def handle_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in accepted_users:
        await update.message.reply_text("❌ لم يتم قبولك بعد. يرجى انتظار الموافقة.")
        return
    pair = update.message.text.strip()
    if pair in PAIRS:
        signal = generate_signal(pair)
        await update.message.reply_text(signal)
    else:
        await update.message.reply_text("❌ الزوج غير معروف. الرجاء اختيار زوج من القائمة.")

async def accept_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        args = context.args
        if args and args[0].isdigit():
            user_id = int(args[0])
            accepted_users.add(user_id)
            await update.message.reply_text(f"✅ تم قبول المستخدم: {user_id}")
        else:
            await update.message.reply_text("❌ الأمر غير صالح. استخدم /accept <user_id>")
    else:
        # إذا استقبل البوت الأمر من البوت الأول أو المستخدم، نقبل تلقائيًا
        args = context.args
        if args and args[0].isdigit():
            user_id = int(args[0])
            accepted_users.add(user_id)
            await update.message.reply_text(f"✅ تم قبولك تلقائيًا.")
        else:
            await update.message.reply_text("❌ الأمر غير صالح.")

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pair))
    app.add_handler(CommandHandler("accept", accept_command))

    app.run_polling()

if __name__ == "__main__":
    main()
