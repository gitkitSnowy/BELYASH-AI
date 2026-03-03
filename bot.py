import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai

# Конфигурация через переменные окружения (для безопасности на хостинге)
TOKEN = os.getenv('TELEGRAM_TOKEN', '8715187751:AAFljEDo1WN_UdwQKy2AEJqeLsQUY3VcI3c')
GEMINI_KEY = os.getenv('GEMINI_KEY', 'AIzaSyAJhic5SwlS7A4Vgpim6uUlt99qQ8ih5dA')

# Настройка нейросети
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Хранилище истории (в оперативной памяти)
user_sessions = {}

logging.basicConfig(level=logging.INFO)

# Главное меню (кнопки)
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🗑 Очистить память", callback_data='clear')],
        [InlineKeyboardButton("🎭 Сменить стиль", callback_data='styles')],
        [InlineKeyboardButton("🆘 Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = [] # Инициализируем историю
    
    welcome_text = (
        f"👋 Здарова, {update.effective_user.first_name}!\n\n"
        "Я — **Belyash AI**. Я не просто бот, я твоя правая рука на базе Gemini.\n"
        "Могу кодить, писать тексты или просто базарить за жизнь.\n\n"
        "👇 Жми кнопки ниже, если хочешь что-то подкрутить."
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # Добавляем сообщение пользователя в историю
    user_sessions[user_id].append({"role": "user", "parts": [text]})
    
    # Ограничиваем память (последние 10 сообщений)
    if len(user_sessions[user_id]) > 10:
        user_sessions[user_id] = user_sessions[user_id][-10:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Отправляем запрос с учетом всей истории (контекста)
        chat_session = model.start_chat(history=user_sessions[user_id][:-1])
        response = chat_session.send_message(text)
        
        bot_response = response.text
        # Добавляем ответ бота в историю
        user_sessions[user_id].append({"role": "model", "parts": [bot_response]})
        
        await update.message.reply_text(bot_response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Ошибка Gemini: {e}")
        await update.message.reply_text("🧨 Ошибка связи с нейронкой. Попробуй через минуту или включи VPN, если ты админ.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'clear':
        user_sessions[user_id] = []
        await query.edit_message_text("🧼 Память очищена! Я всё забыл. Начнем с чистого листа.", reply_markup=main_menu())
    
    elif query.data == 'styles':
        keyboard = [
            [InlineKeyboardButton("🥟 Ровный Беляш", callback_data='style_gop')],
            [InlineKeyboardButton("🎩 Профессор", callback_data='style_prof')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        await query.edit_message_text("Выбери, как мне с тобой общаться:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'back':
        await query.edit_message_text("Меню управления Беляшом:", reply_markup=main_menu())

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Беляш AI запущен 24/7...")
    app.run_polling()
