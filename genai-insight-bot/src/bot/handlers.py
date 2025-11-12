from telegram import Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import io
import os
from analysis.comparator import comparator
from analysis.recommender import recommender
from utils.file_parser import file_parser
from database.operations import db
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when command /start is issued"""
    
    welcome_text = """
🤖 **Добро пожаловать в GenAI Insight Bot!**

Я помогу вам анализировать экспертов в области Generative AI, находить связи и получать инсайты.

**Доступные команды:**

🔍 *Поиск и анализ*
/people [имя] - Найти информацию о человеке
/compare X vs Y - Сравнить двух экспертов
/recommend [тема] - Рекомендовать экспертов по теме
/trends - Показать текущие тренды

📊 *Работа с данными*
/upload - Загрузить файл с данными (CSV, JSON, TXT)
/stats - Показать статистику базы данных

💡 *Инсайты*
/insights - Получить последние инсайты
/network [имя] - Показать сеть связей

**Примеры:**
`/compare Ilya Sutskever vs Yann LeCun`
`/recommend multimodal AI`
`/people Sam Altman`
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare command"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Используйте: `/compare Имя1 vs Имя2`\nПример: `/compare Ilya Sutskever vs Yann LeCun`",
            parse_mode='Markdown'
        )
        return
    
    query = " ".join(context.args)
    if " vs " not in query:
        await update.message.reply_text(
            "❌ Используйте 'vs' для сравнения. Пример: `/compare Имя1 vs Имя2`",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Extract names
        names = query.split(" vs ")
        person_x = names[0].strip()
        person_y = names[1].strip()
        
        # Generate comparison report
        report = await comparator.generate_comparison_report(person_x, person_y)
        
        # Send report (split if too long)
        if len(report) > 4096:
            for i in range(0, len(report), 4096):
                await update.message.reply_text(report[i:i+4096], parse_mode='Markdown')
        else:
            await update.message.reply_text(report, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in compare_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при сравнении. Проверьте имена и попробуйте снова."
        )

async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /recommend command"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите тему для рекомендаций.\nПример: `/recommend large language models`",
            parse_mode='Markdown'
        )
        return
    
    topic = " ".join(context.args)
    
    try:
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Generate recommendations
        report = await recommender.get_recommendation_report(topic)
        
        # Send report
        if len(report) > 4096:
            for i in range(0, len(report), 4096):
                await update.message.reply_text(report[i:i+4096], parse_mode='Markdown')
        else:
            await update.message.reply_text(report, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error in recommend_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при поиске рекомендаций. Попробуйте другую тему."
        )

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file uploads"""
    
    await update.message.reply_text(
        "📁 Отправьте файл (CSV, JSON или TXT) для анализа.\n\n"
        "**Поддерживаемые форматы:**\n"
        "• CSV - таблицы с данными об экспертах\n"
        "• JSON - структурированные данные\n"
        "• TXT - тексты для анализа\n\n"
        "Максимальный размер: 10MB"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded files"""
    
    document = update.message.document
    if not document:
        await update.message.reply_text("❌ Файл не найден.")
        return
    
    # Check file size
    if document.file_size > 10 * 1024 * 1024:  # 10MB
        await update.message.reply_text("❌ Файл слишком большой. Максимум 10MB.")
        return
    
    # Check file type
    file_extension = os.path.splitext(document.file_name)[1].lower()
    if file_extension not in file_parser.get_supported_formats():
        await update.message.reply_text(
            f"❌ Неподдерживаемый формат файла. Поддерживаются: {', '.join(file_parser.get_supported_formats())}"
        )
        return
    
    try:
        # Show uploading status
        await update.message.reply_text("📥 Загружаю и анализирую файл...")
        
        # Get file content
        file = await context.bot.get_file(document.file_id)
        file_content = await file.download_as_bytearray()
        
        # Parse file
        result = await file_parser.parse_file(file_content, document.file_name, file_extension[1:])
        
        # Send results
        if 'error' in result:
            await update.message.reply_text(f"❌ Ошибка: {result['error']}")
        else:
            success_message = f"""
✅ **Файл успешно обработан!**

📊 **Результаты:**
• Людей обработано: {result.get('people_processed', 0)}
• Проектов обработано: {result.get('projects_processed', 0)}
• Публикаций проанализировано: {result.get('publications_processed', 0)}
• Инсайтов найдено: {result.get('insights_found', 0)}

Теперь вы можете использовать команды:
`/recommend [тема]` - для поиска экспертов
`/compare X vs Y` - для сравнения
`/stats` - для просмотра статистики
"""
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке файла.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show database statistics"""
    
    try:
        session = db.get_session()
        
        # Get counts
        people_count = session.query(db.Person).count()
        projects_count = session.query(db.Project).count()
        publications_count = session.query(db.Publication).count()
        skills_count = session.query(db.Skill).count()
        
        stats_text = f"""
📊 **Статистика базы данных:**

👥 Людей: {people_count}
🚀 Проектов: {projects_count}
📝 Публикаций: {publications_count}
🛠 Навыков: {skills_count}

💡 **Используйте:**
`/recommend [тема]` - найти экспертов
`/compare X vs Y` - сравнить людей
`/upload` - добавить данные
"""
        await update.message.reply_text(stats_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in stats_command: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики.")

async def people_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for a specific person"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите имя для поиска.\nПример: `/people Ilya Sutskever`",
            parse_mode='Markdown'
        )
        return
    
    name = " ".join(context.args)
    
    try:
        person = db.get_person_by_name(name)
        
        if not person:
            await update.message.reply_text(f"❌ Человек '{name}' не найден в базе.")
            return
        
        # Format person info
        person_info = f"""
👤 **{person.name}**

🏢 {person.position} @ {person.company}

🎯 **Навыки:** {', '.join([skill.name for skill in person.skills][:5])}
🚀 **Проекты:** {', '.join([project.name for project in person.projects][:3])}

💡 **Используйте:**
`/compare {person.name} vs [другое_имя]`
`/network {person.name}`
"""
        await update.message.reply_text(person_info, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in people_command: {e}")
        await update.message.reply_text("❌ Ошибка при поиске человека.")

def setup_handlers(application):
    """Setup all bot handlers"""
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(CommandHandler("recommend", recommend_command))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("people", people_command))
    
    # File handler
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    # Fallback handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                         lambda u, c: u.message.reply_text(
                                             "Используйте /start для просмотра доступных команд."
                                         )))