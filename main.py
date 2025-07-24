
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ✅ التوكن والمعرف
TOKEN = "8107272693:AAFp2TOAvUunTaPPiSXHgFSVqrSuIJ5Gc4U"
DEVELOPER_ID = 6964741705
API_KEY = "W88S5OTAQIAE42AX"

# 🟢 بيانات الدفع
PAYMENT_INFO = """
🔒 *البوت مدفوع - الاشتراك 5 دولار فقط*

💸 *طرق الدفع:*
1️⃣ USDT (BEP20): `0x3a5db3aec7c262017af9423219eb64b5eb6643d7`
2️⃣ USDT (TRC20): `THrV9BLydZTYKox1MnnAivqitHBEz3xKiq`
3️⃣ Payeer: `P1113622813`

📸 بعد الدفع، أرسل لقطة الشاشة هنا وسيتم مراجعتها من المطور.
"""

# 🗂️ إدارة المستخدمين
approved_users = set()
pending_users = {}

# 📊 أزواج العملات المرتبطة بـ Alpha Vantage
symbol_mapping = {
    "EUR/USD OTC": "EUR/USD",
    "EUR/JPY OTC": "EUR/JPY",
    "EUR/RUB OTC": "EUR/RUB",
    "EUR/TRY OTC": "EUR/TRY",
    "EUR/CHF OTC": "EUR/CHF",
    "EUR/HUF OTC": "EUR/HUF"
}

# 🧠 الحسابات الفنية
def get_market_data(symbol):
    fx_symbol = symbol.replace("/", "")
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={symbol[:3]}&to_symbol={symbol[4:7]}&interval=1min&apikey={API_KEY}&outputsize=compact"
    r = requests.get(url)
    data = r.json()
    try:
        prices = list(data['Time Series FX (1min)'].items())
        closes = [float(v['4. close']) for k, v in prices]
        ema20 = sum(closes[:20]) / 20
        ema50 = sum(closes[:50]) / 50
        rsi = calculate_rsi(closes)
        boll = bollinger_position(closes)
        return ema20, ema50, rsi, boll
    except Exception as e:
        return None, None, None, f"خطأ: {e}"

def calculate_rsi(closes):
    gains = []
    losses = []
    for i in range(1, 15):
        diff = closes[i - 1] - closes[i]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / 14 if gains else 0.01
    avg_loss = sum(losses) / 14 if losses else 0.01
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def bollinger_position(closes):
    ma20 = sum(closes[:20]) / 20
    std = (sum((x - ma20) ** 2 for x in closes[:20]) / 20) ** 0.5
    last_price = closes[0]
    if last_price > ma20 + 2 * std:
        return "أعلى الحد العلوي"
    elif last_price < ma20 - 2 * std:
        return "أسفل الحد السفلي"
    else:
        return "داخل النطاق"

def format_analysis(symbol, ema20, ema50, rsi, boll):
    direction = "صاعد ✅" if ema20 > ema50 else "هابط ❌"
    decision = "شراء (CALL)" if ema20 > ema50 else "بيع (PUT)"
    now = datetime.now().strftime("%I:%M %p")
    return f"""
📊 التوصية: {decision}
💱 الزوج: {symbol}
🔍 التحليل:
🔹 EMA:
- EMA20 = {round(ema20, 4)}
- EMA50 = {round(ema50, 4)}
📈 الاتجاه: {direction}

🔸 RSI = {rsi}
✅ منطقة تداول {"طبيعية" if rsi < 70 else "تشبع"}

🔻 Bollinger Bands: {boll}

📚 شرح المؤشرات:
- EMA20 {'>' if ema20 > ema50 else '<'} EMA50 → {"صعود" if ema20 > ema50 else "هبوط"}
- RSI < 70 → غير مشبع
- Bollinger → يعطي احتمالات الانعكاس

⏱️ الفريم: 1 دقيقة
⏰ التوقيت: {now}
"""

# ✅ بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in approved_users:
        await send_pairs_panel(update, context)
    elif user_id in pending_users:
        await context.bot.send_message(chat_id=user_id, text="⏳ طلبك قيد المراجعة من المطور.")
    else:
        pending_users[user_id] = update.effective_user.username
        await context.bot.send_message(chat_id=user_id, text=PAYMENT_INFO, parse_mode="Markdown")

# 🧾 إرسال صورة الدفع
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in approved_users:
        return
    if user.id not in pending_users:
        await update.message.reply_text("❗ أرسل أولاً /start لبدء الاشتراك.")
        return
    caption = f"📥 إثبات دفع من: @{user.username} ({user.id})"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user.id}"),
         InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user.id}")]
    ])
    await context.bot.send_photo(chat_id=DEVELOPER_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=keyboard)

# 🔘 أزرار الأزواج
async def send_pairs_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in approved_users:
        await update.message.reply_text("❌ هذا البوت خاص بالمشتركين فقط.")
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("EUR/USD OTC", callback_data="pair_EUR/USD OTC"),
         InlineKeyboardButton("EUR/JPY OTC", callback_data="pair_EUR/JPY OTC")],
        [InlineKeyboardButton("EUR/RUB OTC", callback_data="pair_EUR/RUB OTC"),
         InlineKeyboardButton("EUR/TRY OTC", callback_data="pair_EUR/TRY OTC")],
        [InlineKeyboardButton("EUR/HUF OTC", callback_data="pair_EUR/HUF OTC"),
         InlineKeyboardButton("EUR/CHF OTC", callback_data="pair_EUR/CHF OTC")]
    ])
    await context.bot.send_message(chat_id=user_id, text="💱 اختر الزوج الذي تريد الحصول على توصية له:", reply_markup=keyboard)

# ⌨️ الرد على الضغط على الأزواج أو القبول
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
        await context.bot.send_message(chat_id=user_id, text="❌ تم رفض طلبك.")
        await query.edit_message_text("❌ تم رفض المستخدم.")
    elif data.startswith("pair_"):
        symbol = data.replace("pair_", "")
        api_symbol = symbol_mapping.get(symbol, "EUR/USD")
        ema20, ema50, rsi, boll = get_market_data(api_symbol)
        if ema20:
            msg = format_analysis(symbol, ema20, ema50, rsi, boll)
        else:
            msg = f"❌ تعذر جلب بيانات الزوج {symbol} حالياً."
        await context.bot.send_message(chat_id=update.effective_user.id, text=msg)

# 🚀 تشغيل التطبيق
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", send_pairs_panel))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
