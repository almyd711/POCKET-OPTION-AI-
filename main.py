import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import random

# ✅ التوكن ومعرف المطور
TOKEN = os.getenv("8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U")
DEVELOPER_ID = 6964741705

# ✅ بيانات الدفع
PAYMENT_MESSAGE = """🔒 البوت مدفوع: عليك الدفع 5 دولار للاشتراك

💸 وسائل الدفع:
1️⃣ USDT - شبكة BEP20  
📥 العنوان: 0x3a5db3aec7c262017af9423219eb64b5eb6643d7

2️⃣ USDT - شبكة TRC20  
📥 العنوان: THrV9BLydZTYKox1MnnAivqitHBEz3xKiq

3️⃣ Payeer  
📥 المعرف: P1113622813

📷 بعد الدفع، أرسل لقطة شاشة للتحقق.
🕘 التفعيل يتم يدويًا خلال دقائق.
"""

# ✅ الأزواج المدعومة
PAIRS = [
    "USD/CHF", "AUD/USD", "USD/JPY", "USD/CAD",
    "EUR/JPY", "EUR/CAD", "EUR/USD", "EUR/CHF", "EUR/AUD"
]

# ✅ المستخدمون المفعلون
approved_users = set()
pending_requests = {}  # user_id: screenshot_file_id

# ✅ الكيبورد الرئيسي مع أزرار الأزواج وزر عرض الطلبات للمطور
def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton(pair, callback_data=f"pair_{pair}")] for pair in PAIRS]
    if DEVELOPER_ID in approved_users:
        keyboard.append([InlineKeyboardButton("📥 عرض الطلبات", callback_data="view_requests")])
    return InlineKeyboardMarkup(keyboard)

# ✅ حساب نسبة نجاح الصفقة بناءً على القيم الفنية
def calculate_success_rate(ema20, ema50, rsi):
    base_rate = 70
    diff = ema20 - ema50
    if diff > 0.01:
        base_rate += 15
    elif diff > 0.005:
        base_rate += 10
    elif diff > 0.001:
        base_rate += 5
    else:
        base_rate -= 10
    if 30 < rsi < 70:
        base_rate += 10
    else:
        base_rate -= 5
    base_rate = max(0, min(100, base_rate))
    return round(base_rate, 2)

# ✅ تنسيق رسالة التوصية مع نسبة النجاح الحقيقية
def format_recommendation(pair, ema20, ema50, rsi, boll):
    success_rate = calculate_success_rate(ema20, ema50, rsi)
    success_text = f"🎯 نسبة نجاح الصفقة المتوقعة: {success_rate}%"

    return f"""📊 التوصية: شراء (CALL)
💱 الزوج: {pair}
🔍 التحليل:
🔹 EMA:
- EMA20 = {round(ema20, 4)}
- EMA50 = {round(ema50, 4)}
📈 الاتجاه: {'صاعد ✅' if ema20 > ema50 else 'هابط ❌'}

🔸 RSI = {rsi}
✅ منطقة تداول {'طبيعية' if rsi < 70 else 'تشبع'}

🔻 Bollinger Bands: {boll}

📚 شرح المؤشرات:
- EMA20 {'>' if ema20 > ema50 else '<'} EMA50 → {'صعود' if ema20 > ema50 else 'هبوط'}
- RSI < 70 → غير مشبع
- Bollinger → يعطي احتمالات الانعكاس

{success_text}

⏱️ الفريم: 1 دقيقة
⏰ التوقيت: 03:23 PM حسب التوقيت مكة المكرمة"""

# ✅ بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == DEVELOPER_ID:
        approved_users.add(DEVELOPER_ID)
        await update.message.reply_text(
            "👋 مرحباً أيها المطور، يمكنك اختيار الزوج أو إدارة الطلبات.",
            reply_markup=main_menu_keyboard()
        )
    elif user_id in approved_users:
        await update.message.reply_text(
            "✅ تم تفعيل اشتراكك. اختر الزوج لعرض التوصيات:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(PAYMENT_MESSAGE)

# ✅ استقبال صورة إثبات الدفع من المستخدمين الجدد
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id in approved_users:
        return

    photo = update.message.photo[-1]
    pending_requests[user_id] = photo.file_id
    await update.message.reply_text("📥 تم استلام إثبات الدفع. بانتظار التفعيل.")

    await context.bot.send_photo(
        chat_id=DEVELOPER_ID,
        photo=photo.file_id,
        caption=f"🆕 طلب اشتراك جديد:\n👤 المستخدم: {user.full_name}\n🆔 ID: {user_id}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ قبول", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
        ]])
    )

# ✅ التعامل مع أزرار البوت
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data.startswith("pair_"):
        if user_id not in approved_users and user_id != DEVELOPER_ID:
            await query.message.reply_text("🔒 البوت مدفوع. يرجى الدفع أولاً.")
            return
        pair = query.data.replace("pair_", "")
        # هنا افتراضيا قيم ثابتة للتحليل، يمكنك تعديلها لجلب بيانات حقيقية
        ema20 = 1.0889
        ema50 = 1.0775
        rsi = 55.03
        boll = "أسفل الحد السفلي"
        await query.message.reply_text(format_recommendation(pair, ema20, ema50, rsi, boll))

    elif query.data == "view_requests":
        if user_id == DEVELOPER_ID:
            await send_pending_requests(update, context)
        else:
            await query.message.reply_text("❌ هذا الخيار متاح فقط للمطور.")

    elif query.data.startswith("approve_") and user_id == DEVELOPER_ID:
        uid = int(query.data.replace("approve_", ""))
        approved_users.add(uid)
        pending_requests.pop(uid, None)
        await context.bot.send_message(uid, "✅ تم تفعيل اشتراكك! يمكنك الآن استخدام البوت.")
        await query.edit_message_caption(caption="✅ تم قبول الطلب وتفعيل الاشتراك.")

    elif query.data.startswith("reject_") and user_id == DEVELOPER_ID:
        uid = int(query.data.replace("reject_", ""))
        pending_requests.pop(uid, None)
        await context.bot.send_message(uid, "❌ لم يتم قبول الاشتراك حالياً. يمكنك إعادة المحاولة لاحقاً.")
        await query.edit_message_caption(caption="❌ تم رفض الطلب.")

# ✅ عرض الطلبات للمطور
async def send_pending_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pending_requests:
        await update.callback_query.message.reply_text("📭 لا توجد طلبات جديدة حالياً.")
        return
    text = "📄 قائمة الطلبات:\n"
    for uid in pending_requests.keys():
        text += f"- المستخدم ID: {uid}\n"
    await update.callback_query.message.reply_text(text)

# ✅ تشغيل البوت
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if not TOKEN:
        print("❌ يرجى تعيين متغير البيئة BOT_TOKEN قبل التشغيل.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ Bot is running...")
    app.run_polling()
