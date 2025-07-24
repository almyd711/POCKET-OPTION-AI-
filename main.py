
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U"
DEVELOPER_ID = 6964741705

approved_users = set()
pending_users = {}

PAYMENT_INFO = """
🔒 *الدخول مدفوع - 5 دولار فقط*

💸 *طرق الدفع:*
1️⃣ USDT (BEP20): `0x3a5db3aec7c262017af9423219eb64b5eb6643d7`
2️⃣ USDT (TRC20): `THrV9BLydZTYKox1MnnAivqitHBEz3xKiq`
3️⃣ Payeer: `P1113622813`

📸 بعد الدفع، أرسل لقطة الشاشة هنا وسيتم مراجعتها من المطور.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in approved_users:
        await context.bot.send_message(chat_id=user_id, text="✅ تم التفعيل! ستصلك التوصيات قريبًا.")
        # هنا ترسل التوصيات لاحقًا
    elif user_id in pending_users:
        await context.bot.send_message(chat_id=user_id, text="⏳ تم استلام طلبك، يرجى الانتظار للمراجعة.")
    else:
        pending_users[user_id] = update.effective_user.username
        await context.bot.send_message(chat_id=user_id, text=PAYMENT_INFO, parse_mode="Markdown")
        await context.bot.send_message(chat_id=DEVELOPER_ID,
            text=f"📥 طلب دخول جديد من: @{update.effective_user.username} ({user_id})",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
                 InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")]
            ])
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("accept_"):
        user_id = int(data.split("_")[1])
        approved_users.add(user_id)
        await context.bot.send_message(chat_id=user_id, text="✅ تم قبولك! يمكنك الآن استخدام البوت.")
        await query.edit_message_text("✅ تم قبول المستخدم.")
    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        if user_id in pending_users:
            await context.bot.send_message(chat_id=user_id, text="❌ تم رفض طلبك. إذا كنت تعتقد أن هناك خطأ، تواصل مع المطور.")
        await query.edit_message_text("❌ تم رفض المستخدم.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
