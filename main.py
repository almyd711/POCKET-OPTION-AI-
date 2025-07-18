
# ✅ Telegram Multi-Function Bot - دمج الدفع والتوصيات

import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ✅ التوكن ومعرف المطور
TOKEN = "8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U"
ADMIN_ID = 6964741705

# ✅ الأزواج المتاحة للتوصيات
PAIRS = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC"]

# ✅ المستخدمين المفعلين
approved_users = set()

# ✅ مولد بيانات التوصيات
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
    return f"""📊 التوصية: {reco}
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

# ✅ شاشة الدفع
def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Binance", callback_data='binance'),
         InlineKeyboardButton("💳 Payeer", callback_data='payeer')]
    ])

# ✅ دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in approved_users:
        keyboard = [[pair] for pair in PAIRS]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ تم التفعيل!
اختر زوج العملات:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "👋 مرحباً بك!
💰 يرجى اختيار طريقة الدفع لإتمام التفعيل:",
            reply_markup=payment_keyboard()
        )

# ✅ عرض تفاصيل الدفع
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'binance':
        await query.message.reply_text(
            "📤 *تحويل 5 USDT عبر شبكة BEP20:*

"
            "💼 *العنوان:* `0x3a5db3aec7c262017af9423219eb64b5eb6643d7`
"
            "🌐 *الشبكة:* BEP20
💰 *المبلغ:* 5 USDT

"
            "✅ أرسل إثبات الدفع هنا مباشرة.
📌 سيتم المراجعة خلال دقائق.",
            parse_mode="Markdown"
        )
    elif query.data == 'payeer':
        await query.message.reply_text(
            "📤 *لتحويل 5 دولار عبر Payeer:*

"
            "💳 *رقم الحساب:* `P1122334455`
💰 *المبلغ:* 5 USD
📝 *الملاحظة:* [خدمة اشتراك]

"
            "✅ أرسل إثبات الدفع هنا مباشرة.",
            parse_mode="Markdown"
        )

# ✅ استقبال الإثبات
async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
    await update.message.reply_text("✅ تم استلام إثبات الدفع.
🕐 سيتم المراجعة من قبل الإدارة.")

# ✅ تفعيل المستخدم يدوياً عبر المطور
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        approved_users.add(user_id)
        await update.message.reply_text(f"✅ تم تفعيل المستخدم: {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

# ✅ عند إرسال الزوج
async def handle_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in approved_users:
        await update.message.reply_text("🚫 لا يمكنك استخدام التوصيات حتى يتم تفعيلك بعد الدفع.")
        return

    pair = update.message.text.strip()
    if pair in PAIRS:
        await update.message.reply_text(generate_signal(pair))
    else:
        await update.message.reply_text("❌ الزوج غير معروف. الرجاء اختيار زوج من القائمة.")

# ✅ بدء التشغيل
def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND, handle_payment_proof))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pair))
    app.run_polling()

if __name__ == "__main__":
    main()
