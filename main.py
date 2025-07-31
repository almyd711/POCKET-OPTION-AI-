import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

# ✅ معلومات الدخول
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6964741705
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# ✅ إعدادات الأزواج
PAIRS = {
    "USD/CHF": "USDCHF",
    "AUD/USD": "AUDUSD",
    "USD/JPY": "USDJPY",
    "USD/CAD": "USDCAD",
    "EUR/JPY": "EURJPY",
    "EUR/CAD": "EURCAD",
    "EUR/USD": "EURUSD",
    "EUR/CHF": "EURCHF",
    "EUR/AUD": "EURAUD"
}

# ✅ إعداد السجل
logging.basicConfig(level=logging.INFO)

# ✅ التحقق من الاشتراك
def is_subscribed(user_id):
    return str(user_id) == str(ADMIN_ID)

# ✅ حساب نسبة النجاح (تقديرية)
def calculate_success_probability(rsi, bb_signal, ema_signal):
    score = 0
    if 45 <= rsi <= 70:
        score += 1
    if bb_signal.lower() in ["انعكاس محتمل", "قرب من الحد السفلي", "قرب من الحد العلوي"]:
        score += 1
    if ema_signal in ["صاعد", "هابط"]:
        score += 1
    return int((score / 3) * 100)

# ✅ إرسال التوصية
async def send_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE, pair, symbol_code):
    now = datetime.now().strftime("%I:%M %p")

    # بيانات وهمية كمثال
    analysis = {
        'ema_signal': 'صعود - EMA20 أعلى من EMA50',
        'bb_signal': 'انعكاس محتمل',
        'rsi': 58.23,
    }
    analysis['chance'] = calculate_success_probability(analysis['rsi'], analysis['bb_signal'], analysis['ema_signal'])

    message = f"""
📊 التوصية: شراء (CALL)
💱 الزوج: {pair}
🔍 التحليل:

🔹 EMA:
- {analysis['ema_signal']}

🔸 RSI = {analysis['rsi']:.2f}
✅ منطقة تداول طبيعية

🔻 Bollinger Bands: {analysis['bb_signal']}

📚 شرح المؤشرات:
- {analysis['ema_signal']}
- RSI لتحديد مناطق التشبع
- Bollinger يعطي احتمالات الانعكاس

🎯 نسبة نجاح متوقعة: {analysis['chance']}%
⏱️ الفريم: 1 دقيقة
⏰ التوقيت: {now}
"""
    await update.callback_query.message.reply_text(message.strip())

# ✅ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_subscribed(user_id):
        await update.message.reply_text("❌ لم يتم تفعيل اشتراكك بعد.\n💳 استخدم /buy لشراء الاشتراك.")
        return
    keyboard = [[InlineKeyboardButton(pair, callback_data=pair)] for pair in PAIRS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 مرحباً، اختر زوج التداول لبدء التوصيات:", reply_markup=reply_markup)

# ✅ /pair
async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_subscribed(user_id):
        await update.message.reply_text("❌ تحتاج إلى اشتراك مفعل لاستخدام هذا الأمر.\n💳 استخدم /buy.")
        return
    keyboard = [[InlineKeyboardButton(pair, callback_data=pair)] for pair in PAIRS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔽 اختر زوج العملات:", reply_markup=reply_markup)

# ✅ /timeframe
async def timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_subscribed(user_id):
        await update.message.reply_text("❌ تحتاج إلى اشتراك مفعل لاستخدام هذا الأمر.\n💳 استخدم /buy.")
        return
    keyboard = [
        [InlineKeyboardButton("1 دقيقة", callback_data="1m")],
        [InlineKeyboardButton("2 دقيقة", callback_data="2m")],
        [InlineKeyboardButton("5 دقيقة", callback_data="5m")],
    ]
    await update.message.reply_text("🕒 اختر الفريم الزمني:", reply_markup=InlineKeyboardMarkup(keyboard))

# ✅ /buy
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
💳 لشراء الاشتراك، يرجى إرسال 5 USDT إلى أحد العناوين التالية:

🔗 BEP20: `0x3a5db3aec7c262017af9423219eb64b5eb6643d7`  
🔗 TRC20: `THrV9BLydZTYKox1MnnAivqitHBEz3xKiq`  
💼 Payeer: `P1113622813`

بعد الدفع، أرسل لقطة الشاشة إلى المطور ليتم التفعيل يدويًا ✅
""")

# ✅ /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_subscribed(user_id):
        await update.message.reply_text("✅ اشتراكك مفعل.")
    else:
        await update.message.reply_text("❌ لم يتم تفعيل اشتراكك بعد.\n💳 استخدم /buy.")

# ✅ /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
ℹ️ أوامر البوت المتاحة:
/start - بدء البوت
/buy - شراء الاشتراك
/pair - اختيار زوج العملات
/timeframe - اختيار الفريم الزمني
/status - حالة اشتراكك
/help - المساعدة والدعم
""")

# ✅ عند اختيار الزوج
async def handle_pair_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_subscribed(user_id):
        await query.message.reply_text("❌ تحتاج إلى اشتراك مفعل.\n💳 استخدم /buy.")
        return
    await query.answer()
    pair = query.data
    symbol_code = PAIRS.get(pair)
    if symbol_code:
        await send_recommendation(update, context, pair, symbol_code)

# ✅ تشغيل البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("pair", pair))
    app.add_handler(CommandHandler("timeframe", timeframe))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_pair_choice))

    app.run_polling()
