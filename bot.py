import logging
import json
import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from datetime import datetime
import random

TOKEN = os.getenv("8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6964741705"))  # ضع معرف المدير في متغير البيئة ADMIN_ID

PAIRS = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC"]

PAYMENTS_FILE = "payments.json"
APPROVED_FILE = "approved.json"

# تحميل البيانات من ملفات JSON
def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

payments = load_json(PAYMENTS_FILE, {})
approved_users = set(load_json(APPROVED_FILE, []))

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
    user_id = update.effective_user.id
    if user_id in approved_users:
        keyboard = [[pair] for pair in PAIRS]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 مرحباً بك! اختر الزوج الذي تريد التوصيات عليه:", reply_markup=reply_markup)
    else:
        keyboard = [
            [
                InlineKeyboardButton("💸 Binance", callback_data='binance'),
                InlineKeyboardButton("💳 Payeer", callback_data='payeer')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👋 مرحباً بك!\n💰 اختر طريقة الدفع لإتمام العملية:", reply_markup=reply_markup)

async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'binance':
        msg = (
            f"📤 *تحويل 5 USDT عبر شبكة BEP20 (BNB Smart Chain):*\n\n"
            f"💼 *العنوان:* `0x3a5db3aec7c262017af9423219eb64b5eb6643d7`\n"
            f"🌐 *الشبكة:* BNB Smart Chain (BEP20)\n"
            f"💰 *المبلغ:* 5 USDT\n"
            f"🆔 *معرف المستخدم:* `{user_id}`\n\n"
            f"💡 *ملاحظة:* تأكد من اختيار الشبكة الصحيحة لتجنب فقدان الأموال."
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif query.data == 'payeer':
        msg = (
            f"📤 *لتحويل 5 دولار عبر محفظة Payeer:*\n\n"
            f"💳 *رقم الحساب:* `P1122334455`\n"
            f"💰 *المبلغ:* 5 USD\n"
            f"📝 *الملاحظة:* [خدمة اشتراك]\n"
            f"🌐 *العملة:* الدولار الأمريكي (USD)\n\n"
            f"✅ *تأكد من إرسال المبلغ من محفظة Payeer أو من موقع يدعمه.*"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    await query.message.reply_text("📸 يرجى إرسال إثبات الدفع (صورة أو رسالة نصية) هنا.")

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "لا يوجد"

    # إعادة توجيه الإثبات للمدير
    await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=chat_id, message_id=update.message.message_id)

    # تسجيل الدفع مع حالة معلقة
    payments[str(user_id)] = {
        "username": username,
        "message_id": update.message.message_id,
        "status": "pending"
    }
    save_json(PAYMENTS_FILE, payments)

    await update.message.reply_text("✅ تم استلام إثبات الدفع.\n🕐 سيتم التحقق منه من قبل الإدارة خلال دقائق.")

async def admin_view_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 هذه الأوامر خاصة بالمدير فقط.")
        return

    pending_users = [uid for uid, info in payments.items() if info["status"] == "pending"]

    if not pending_users:
        await update.message.reply_text("لا يوجد طلبات دفع معلقة حالياً.")
        return

    for uid in pending_users:
        info = payments[uid]
        text = f"معرف المستخدم: {uid}\nاسم المستخدم: @{info['username']}\nحالة الدفع: {info['status']}"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"approve_{uid}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{uid}")
            ]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)

async def admin_handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("🚫 هذه الأوامر خاصة بالمدير فقط.")
        return

    data = query.data
    if data.startswith("approve_"):
        uid = data.split("_")[1]
        if uid in payments:
            payments[uid]["status"] = "approved"
            save_json(PAYMENTS_FILE, payments)
            approved_users.add(int(uid))
            save_json(APPROVED_FILE, list(approved_users))
            await query.edit_message_text(f"تم قبول الدفع للمستخدم {uid}.")
            try:
                await context.bot.send_message(int(uid), "🎉 تم تفعيل حسابك بنجاح! يمكنك الآن طلب التوصيات عبر اختيار الزوج.")
            except:
                pass

    elif data.startswith("reject_"):
        uid = data.split("_")[1]
        if uid in payments:
            payments[uid]["status"] = "rejected"
            save_json(PAYMENTS_FILE, payments)
            await query.edit_message_text(f"تم رفض الدفع للمستخدم {uid}.")
            try:
                await context.bot.send_message(int(uid),
                    "❌ تم رفض إثبات الدفع. الرجاء إعادة المحاولة أو الاتصال بالدعم.")
            except:
                pass

async def handle_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in approved_users:
        await update.message.reply_text("❌ يرجى إتمام الدفع أولاً باستخدام /start لاختيار طريقة الدفع.")
        return

    pair = update.message.text.strip()
    if pair in PAIRS:
        signal = generate_signal(pair)
        await update.message.reply_text(signal)
    else:
        await update.message.reply_text("❌ الزوج غير معروف. الرجاء اختيار زوج من القائمة.")

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_payment_method, pattern="^(binance|payeer)$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_payment_proof))

    app.add_handler(CommandHandler("pending", admin_view_pending))
    app.add_handler(CallbackQueryHandler(admin_handle_approval, pattern="^(approve|reject)_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pair))

    app.run_polling()

if __name__ == "__main__":
    main()
