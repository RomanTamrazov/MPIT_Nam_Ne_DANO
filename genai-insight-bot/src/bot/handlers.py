from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **GenAI Insight Bot**\n\n"
        "Бот для анализа экспертов AI.\n"
        "Используйте /stats для статистики."
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Статистика: Бот работает!")

async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите тему: /recommend [тема]")
        return
    topic = " ".join(context.args)
    await update.message.reply_text(f"🔍 Рекомендации по теме: {topic}")

async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используйте: /compare [имя1] vs [имя2]")
        return
    query = " ".join(context.args)
    await update.message.reply_text(f"🆚 Сравнение: {query}")

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📁 Отправьте CSV файл с экспертами")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Файл получен!")

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("recommend", recommend_command))
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    logger.info("✅ Bot handlers configured")