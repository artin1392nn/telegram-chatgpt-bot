# bot.py
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai
import asyncio

# ======= تنظیم کلیدها =======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_KEY

# ======= نگهداری تاریخچه =======
CONTEXTS = {}  # {user_id: [{"role":"user","content":...}, ...]}
MAX_HISTORY = 6  # تعداد پیام‌هایی که ذخیره میشه

# ======= تماس با OpenAI =======
async def call_openai(messages):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=512,
        temperature=0.7
    )
    return resp["choices"][0]["message"]["content"].strip()

# ======= فرمان‌ها =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات چت هستم. پیام بفرست :)")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    CONTEXTS.pop(uid, None)
    await update.message.reply_text("تاریخچه پاک شد.")

# ======= دریافت پیام کاربران =======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    if not text:
        return

    # اضافه کردن پیام کاربر به تاریخچه
    ctx = CONTEXTS.get(uid, [])
    ctx.append({"role":"user","content": text})
    if len(ctx) > MAX_HISTORY * 2:
        ctx = ctx[-MAX_HISTORY*2:]

    # قالب پیام برای OpenAI
    messages = [{"role":"system","content":"You are a helpful assistant answering in Persian."}] + ctx

    try:
        reply = await asyncio.to_thread(call_openai, messages)
    except Exception as e:
        await update.message.reply_text("مشکل در تماس با سرویس. بعداً امتحان کن.")
        return

    ctx.append({"role":"assistant","content": reply})
    CONTEXTS[uid] = ctx
    await update.message.reply_text(reply)

# ======= اجرای ربات =======
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات آماده و اجرا شد!")
    app.run_polling()
