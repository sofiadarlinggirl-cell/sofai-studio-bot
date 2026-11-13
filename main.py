
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8287961182"))

logging.basicConfig(level=logging.INFO)
SERVICE, DESCRIPTION, BUDGET, DEADLINE, CONTACT = range(5)

MENU = [
    ["🎬 Создать ИИ-видео", "📢 Реклама для бизнеса"],
    ["✨ Оживить фото", "🎅 Персональное поздравление"],
    ["💰 Стоимость", "🎞 Портфолио"],
    ["📩 Связаться с Софьей"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(MENU, resize_keyboard=True)
    await update.message.reply_text(
        "🤎 Добро пожаловать в SOF AI STUDIO!\n\n"
        "Создаём стильные ИИ-видео, рекламу и творческие проекты.\n"
        "Выбери, что тебя интересует:",
        reply_markup=keyboard
    )

async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Что хочешь заказать?")
    return SERVICE

async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service"] = update.message.text
    await update.message.reply_text("Расскажи подробнее, какое видео или результат тебе нужен?")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Какой у тебя примерный бюджет? Если пока не определился, так и напиши.")
    return BUDGET

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("К какому сроку нужна работа?")
    return DEADLINE

async def deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["deadline"] = update.message.text
    await update.message.reply_text("Оставь свой Telegram или другой способ связи.")
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
    await update.message.reply_text("Оформление заявки отменено.")
    return ConversationHandler.END

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Стоимость рассчитывается индивидуально "
        "в зависимости от задачи и сложности проекта.\n"
        "Напиши заявку, и Софья подберёт вариант."
    )

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎞 Портфолио SOF AI STUDIO\n"
        "Примеры работ можно посмотреть в нашем канале:\n"
        "https://t.me/aisofstudio"
    )

async def contact_sofia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📩 Написать Софье: @sof_kaai")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN")

    app = Application.builder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(
                    "^(🎬 Создать ИИ-видео|📢 Реклама для бизнеса|✨ Оживить фото|🎅 Персональное поздравление)$"
                ),
                order_start
            )
        ],
        states={
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deadline)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", order_start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("contact", contact_sofia))
    app.add_handler(conversation)
    app.add_handler(MessageHandler(filters.Regex("^💰 Стоимость$"), price))
    app.add_handler(MessageHandler(filters.Regex("^🎞 Портфолио$"), portfolio))
    app.add_handler(MessageHandler(filters.Regex("^📩 Связаться с Софьей$"), contact_sofia))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
