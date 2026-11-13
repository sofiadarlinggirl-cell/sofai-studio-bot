
import os
import asyncio
import secrets
import logging

from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
BASE_URL = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")
PORT = int(os.environ.get("PORT", "10000"))

WEBHOOK_SECRET = secrets.token_urlsafe(32)

DESCRIPTION, BUDGET, DEADLINE, CONTACT = range(4)

MENU = [
    ["🎬 Создать ИИ-видео", "📢 Реклама для бизнеса"],
    ["✨ Оживить фото", "🎅 Персональное поздравление"],
    ["💰 Стоимость", "🎞 Портфолио"],
    ["📩 Связаться с Софьей"],
]

ORDER_BUTTONS = [
    "🎬 Создать ИИ-видео",
    "📢 Реклама для бизнеса",
    "✨ Оживить фото",
    "🎅 Персональное поздравление",
]

bot_app = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(MENU, resize_keyboard=True)
    await update.message.reply_text(
        "🤎 Добро пожаловать в SOF AI STUDIO!\n\n"
        "Создаём стильные ИИ-видео, рекламу и творческие проекты.\n\n"
        "Выбери интересующую услугу:",
        reply_markup=keyboard,
    )


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    context.user_data["service"] = (
        choice if choice in ORDER_BUTTONS else "Индивидуальный заказ"
    )
    await update.message.reply_text(
        "Расскажи подробнее, что именно ты хочешь заказать?"
    )
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Какой у тебя примерный бюджет?")
    return BUDGET


async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("К какому сроку нужна работа?")
    return DEADLINE


async def deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["deadline"] = update.message.text
    await update.message.reply_text(
        "Оставь свой Telegram или другой способ связи."
    )
    return CONTACT


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = context.user_data

    message = (
        "🤎 НОВАЯ ЗАЯВКА SOF AI STUDIO\n\n"
        f"Услуга: {data.get('service')}\n"
        f"Описание: {data.get('description')}\n"
        f"Бюджет: {data.get('budget')}\n"
        f"Срок: {data.get('deadline')}\n"
        f"Контакт: {update.message.text}\n\n"
        f"Клиент: @{user.username or 'не указан'}\n"
        f"Имя: {user.full_name}\n"
        f"ID: {user.id}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    await update.message.reply_text(
        "Спасибо за заявку! 🤎\n"
        "Софья получила твой запрос и скоро свяжется с тобой."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Заявка отменена.")
    return ConversationHandler.END


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Стоимость зависит от задачи и сложности проекта.\n"
        "Оставь заявку, и Софья подберёт подходящий вариант."
    )


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎞 Портфолио SOF AI STUDIO:\nhttps://t.me/aisofstudio"
    )


async def contact_sofia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📩 Написать Софье: @sof_kaai")


def setup_handlers():
    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("order", order_start),
            MessageHandler(filters.Regex(
                r"^(🎬 Создать ИИ-видео|📢 Реклама для бизнеса|✨ Оживить фото|🎅 Персональное поздравление)$"
            ), order_start),
        ],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deadline)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("price", price))
    bot_app.add_handler(CommandHandler("portfolio", portfolio))
    bot_app.add_handler(CommandHandler("contact", contact_sofia))
    bot_app.add_handler(conversation)
    bot_app.add_handler(MessageHandler(filters.Regex(r"^💰 Стоимость$"), price))
    bot_app.add_handler(MessageHandler(filters.Regex(r"^🎞 Портфолио$"), portfolio))
    bot_app.add_handler(MessageHandler(filters.Regex(r"^📩 Связаться с Софьей$"), contact_sofia))


async def webhook(request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        raise web.HTTPForbidden()

    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
    except Exception:
        logging.exception("Webhook update failed")
        raise web.HTTPBadRequest()

    return web.Response(text="ok")


async def on_startup(app):
    await bot_app.initialize()
    setup_handlers()
    await bot_app.start()
    await bot_app.bot.set_webhook(
        url=f"{BASE_URL}/webhook",
        secret_token=WEBHOOK_SECRET,
    )
    logging.info("SOF AI STUDIO bot started")


async def on_cleanup(app):
    await bot_app.bot.delete_webhook()
    await bot_app.stop()
    await bot_app.shutdown()


def main():
    server = web.Application()
    server.router.add_get("/", lambda request: web.Response(text="SOF AI STUDIO is running"))
    server.router.add_post("/webhook", webhook)
    server.on_startup.append(on_startup)
    server.on_cleanup.append(on_cleanup)
    web.run_app(server, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
