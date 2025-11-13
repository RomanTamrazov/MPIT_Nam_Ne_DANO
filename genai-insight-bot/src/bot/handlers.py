from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import logging
from utils.file_parser import file_parser
from database.operations import db
from utils.visualizer import visualizer
import tempfile
import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

def get_main_keyboard():
    """Основная клавиатура с главными командами"""
    keyboard = [
        ['🎯 Рекомендации', '🔍 Поиск'],
        ['⚖️ Сравнить', '📊 Статистика'],
        ['📁 Загрузить данные', '🛠 Очистка'],
        ['📈 Визуализации', 'ℹ️ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура только с отменой"""
    keyboard = [['❌ Отмена']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_visualization_keyboard():
    """Клавиатура для визуализаций"""
    keyboard = [
        ['📊 График рекомендаций', '🔗 Граф связей'],
        ['🎯 Тепловая карта', '🏢 Диаграмма компаний'],
        ['❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cleanup_keyboard():
    """Клавиатура для очистки"""
    keyboard = [
        ['🧹 Очистить дубликаты', '❌ Полная очистка'],
        ['❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_TOPIC, WAITING_SEARCH, WAITING_COMPARE = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **GenAI Insight Bot**

Бот для анализа экспертов в области AI и машинного обучения.

🔍 **Основные возможности:**
• Рекомендации экспертов по темам
• Сравнение специалистов  
• Анализ навыков и компетенций
• Визуализация данных

👇 **Используйте кнопки ниже или команды:**
"""
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **GenAI Insight Bot - Помощь**

👇 **Используйте кнопки или команды:**

**🎯 Рекомендации** `/recommend [тема]`
**🔍 Поиск** `/search [запрос]` 
**⚖️ Сравнить** `/compare [X] vs [Y]`
**📊 Статистика** `/stats`

**📁 Загрузить данные** `/upload`
**🛠 Очистка** `/cleanup` `/clear`
**📈 Визуализации** `/visualize`

**❌ Отмена** `/cancel` - вернуться в главное меню
"""
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    """Показывает расширенную статистику базы данных"""
    try:
        people = db.get_all_people(telegram_id)
        
        if not people:
            await update.message.reply_text(
                "📊 База данных пуста. Используйте /upload для добавления данных.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Считаем уникальных экспертов по имени
        unique_names = set()
        unique_people_map = {}
        
        for person in people:
            normalized_name = person.name.lower().strip()
            unique_names.add(normalized_name)
            if normalized_name not in unique_people_map:
                unique_people_map[normalized_name] = person
        
        unique_people_list = list(unique_people_map.values())
        duplicate_count = len(people) - len(unique_people_list)
        
        # Анализ данных
        companies = {}
        skills_count = {}
        positions_count = {}
        
        for person in unique_people_list:
            # Статистика по компаниям
            company = person.company or "Не указана"
            companies[company] = companies.get(company, 0) + 1
            
            # Статистика по навыкам
            for skill in person.skills:
                skills_count[skill] = skills_count.get(skill, 0) + 1
            
            # Статистика по должностям
            position = person.position or "Не указана"
            positions_count[position] = positions_count.get(position, 0) + 1
        
        # Топ значения
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
        top_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:8]
        top_positions = sorted(positions_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Генерация инсайтов
        insights = []
        if top_companies and top_companies[0][0] != "Не указана":
            insights.append(f"🏢 **{top_companies[0][0]}** - лидер по количеству экспертов")
        if top_skills:
            insights.append(f"🛠 **{top_skills[0][0]}** - самый популярный навык")
        
        # Анализ качества данных
        companies_with_data = len([c for c in companies.keys() if c != "Не указана"])
        positions_with_data = len([p for p in positions_count.keys() if p != "Не указана"])
        
        stats_text = f"""
📊 **Расширенная статистика**

👥 **Уникальных экспертов:** {len(unique_people_list)}
📝 **Всего записей в базе:** {len(people)}
🏭 **Компаний:** {companies_with_data}
👔 **Должностей:** {positions_with_data}

🔍 **Инсайты:**
{chr(10).join(f'• {insight}' for insight in insights) if insights else '• Загрузите больше данных для анализа'}

🏢 **Топ компаний:**
{chr(10).join(f'• {company}: {count}' for company, count in top_companies)}

🛠 **Популярные навыки:**
{chr(10).join(f'• {skill}: {count}' for skill, count in top_skills)}

👔 **Основные должности:**
{chr(10).join(f'• {position}: {count}' for position, count in top_positions)}
"""
        # Добавляем предупреждение о дубликатах только если они есть
        if duplicate_count > 0:
            stats_text += f"\n⚠️ **Обнаружено {duplicate_count} дубликатов**\n💡 Используйте `/cleanup` для очистки"
        
        await update.message.reply_text(
            stats_text, 
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in stats_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении статистики.",
            reply_markup=get_main_keyboard()
        )

async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    """Рекомендует экспертов по заданной теме"""
    # Если команда вызвана через кнопку, запрашиваем тему
    if not context.args and update.message.text == '🎯 Рекомендации':
        await update.message.reply_text(
            "🎯 Введите тему для рекомендаций:\n\nПример: AI, Computer Vision, NLP",
            reply_markup=get_cancel_keyboard()
        )
        return WAITING_TOPIC
    
    if not context.args and update.message.text != '🎯 Рекомендации':
        await update.message.reply_text(
            "Укажите тему: /recommend [тема]\nИли используйте кнопку '🎯 Рекомендации'",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем тему из аргументов или текста сообщения
    if context.args:
        topic = " ".join(context.args).lower().strip()
    else:
        topic = update.message.text.lower().strip()
    
    try:
        await update.message.chat.send_action(action="typing")
        
        # Получаем всех экспертов из базы
        people = db.get_all_people(telegram_id)
        
        if not people:
            await update.message.reply_text(
                "❌ База данных пуста. Сначала загрузите данные через /upload",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        # Улучшенный поиск экспертов по теме
        matched_experts = []
        seen_names = set()
        
        for person in people:
            # Пропускаем дубликаты
            if person.name in seen_names:
                continue
                
            score = 0
            matches = []
            
            # 1. Поиск по имени (точное совпадение)
            if topic in person.name.lower():
                score += 3
                matches.append("имя")
            
            # 2. Поиск по должности (частичное совпадение)
            if person.position:
                position_lower = person.position.lower()
                # Точное совпадение
                if topic in position_lower:
                    score += 2
                    matches.append("должность")
                # Поиск по словам
                elif any(word in position_lower for word in topic.split() if len(word) > 2):
                    score += 1
                    matches.append("должность")
            
            # 3. Поиск по компании (частичное совпадение)
            if person.company:
                company_lower = person.company.lower()
                if topic in company_lower:
                    score += 2
                    matches.append("компания")
                elif any(word in company_lower for word in topic.split() if len(word) > 2):
                    score += 1
                    matches.append("компания")
            
            # 4. Поиск по навыкам (расширенный)
            skill_matches = []
            for skill in person.skills:
                skill_lower = skill.lower()
                # Точное совпадение
                if topic in skill_lower:
                    skill_matches.append(skill)
                    score += 2
                # Поиск по словам
                elif any(word in skill_lower for word in topic.split() if len(word) > 2):
                    skill_matches.append(skill)
                    score += 1
                # Поиск по синонимам для популярных тем
                elif await _check_skill_synonyms(topic, skill_lower):
                    skill_matches.append(skill)
                    score += 1
            
            if skill_matches:
                matches.append(f"навыки: {', '.join(skill_matches[:3])}")
            
            # 5. Поиск по проектам (расширенный)
            project_matches = []
            for project in person.projects:
                project_lower = project.lower()
                if topic in project_lower:
                    project_matches.append(project)
                    score += 2
                elif any(word in project_lower for word in topic.split() if len(word) > 2):
                    project_matches.append(project)
                    score += 1
            
            if project_matches:
                matches.append(f"проекты: {', '.join(project_matches[:2])}")
            
            # 6. Поиск по связанным темам
            if score == 0:
                # Проверяем связанные темы
                related_score = await _check_related_topics(topic, person)
                if related_score > 0:
                    score = related_score
                    matches.append("связанная тема")
            
            # Если нашли совпадения, добавляем эксперта (даже с низким score)
            if score > 0:
                matched_experts.append({
                    'person': person,
                    'score': score,
                    'matches': matches
                })
                seen_names.add(person.name)
        
        # Сортируем по релевантности
        matched_experts.sort(key=lambda x: x['score'], reverse=True)
        
        # Формируем ответ
        if not matched_experts:
            # Показываем всех экспертов если ничего не найдено
            await _show_all_experts_fallback(update, topic, people)
            return ConversationHandler.END

        # Подготавливаем данные для визуализации
        recommendations_data = []
        for expert in matched_experts[:10]:
            recommendations_data.append({
                'name': expert['person'].name,
                'position': expert['person'].position or 'Не указана',
                'company': expert['person'].company or 'Не указана',
                'skills': expert['person'].skills,
                'score': expert['score'],
                'matches': expert['matches']
            })

        # Создаем визуализации если есть рекомендации
        if recommendations_data:
            try:
                # 1. Визуализация рекомендаций (столбчатая диаграмма)
                chart_html = visualizer.create_recommendations_chart(recommendations_data)
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(chart_html)
                    temp_file1 = f.name

                await update.message.reply_document(
                    document=open(temp_file1, 'rb'),
                    filename=f"recommendations_chart_{topic}.html",
                    caption=f"📊 Диаграмма рекомендаций по теме: {topic}"
                )
                os.unlink(temp_file1)
                
                # 2. Визуализация графа связей (если достаточно экспертов)
                if len(recommendations_data) >= 3:
                    connections = []
                    people_data_for_graph = []
                    
                    for expert in matched_experts[:8]:
                        people_data_for_graph.append({
                            'name': expert['person'].name,
                            'company': expert['person'].company or 'Не указана',
                            'skills': expert['person'].skills,
                            'position': expert['person'].position or 'Не указана'
                        })
                    
                    for i in range(len(people_data_for_graph)):
                        for j in range(i + 1, len(people_data_for_graph)):
                            common_skills = set(people_data_for_graph[i]['skills']) & set(people_data_for_graph[j]['skills'])
                            if common_skills:
                                connections.append((i, j))
                            elif (people_data_for_graph[i]['company'] == people_data_for_graph[j]['company'] and 
                                  people_data_for_graph[i]['company'] != 'Не указана'):
                                connections.append((i, j))
                    
                    graph_html = visualizer.create_network_graph(people_data_for_graph, connections)
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                        f.write(graph_html)
                        temp_file2 = f.name

                    await update.message.reply_document(
                        document=open(temp_file2, 'rb'),
                        filename=f"network_graph_{topic}.html",
                        caption=f"🔗 Граф связей экспертов по теме: {topic}"
                    )
                    os.unlink(temp_file2)
                
                # 3. Тепловая карта навыков (если есть навыки)
                skills_data = []
                for expert in matched_experts[:15]:
                    if expert['person'].skills:
                        skills_data.append({
                            'name': expert['person'].name,
                            'skills': expert['person'].skills,
                            'company': expert['person'].company or 'Не указана'
                        })
                
                if skills_data:
                    heatmap_html = visualizer.create_skills_heatmap(skills_data)
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                        f.write(heatmap_html)
                        temp_file3 = f.name

                    await update.message.reply_document(
                        document=open(temp_file3, 'rb'),
                        filename=f"skills_heatmap_{topic}.html",
                        caption=f"🎯 Навыки экспертов по теме: {topic}"
                    )
                    os.unlink(temp_file3)
                
                # 4. Диаграмма компаний
                company_data = []
                for expert in matched_experts:
                    company_data.append({
                        'name': expert['person'].name,
                        'company': expert['person'].company or 'Не указана',
                        'position': expert['person'].position or 'Не указана'
                    })
                
                company_html = visualizer.create_company_distribution(company_data)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(company_html)
                    temp_file4 = f.name

                await update.message.reply_document(
                    document=open(temp_file4, 'rb'),
                    filename=f"companies_{topic}.html",
                    caption=f"🏢 Компании экспертов по теме: {topic}"
                )
                os.unlink(temp_file4)
                
            except Exception as e:
                logger.error(f"Error creating visualization: {e}")
                await update.message.reply_text("⚠️ Визуализации временно недоступны, но вот текстовые рекомендации:")
        
        # Основные рекомендации (топ-5)
        top_experts = matched_experts[:5]
        
        # Формируем простой текст без Markdown форматирования
        response = f"🎯 Рекомендации по теме: {topic}\n\n"
        response += f"📊 Найдено уникальных экспертов: {len(matched_experts)}\n\n"
        
        for i, expert_data in enumerate(top_experts, 1):
            person = expert_data['person']
            matches = expert_data['matches']
            
            response += f"{i}. {person.name}\n"
            response += f"   🏢 {person.position or 'Должность не указана'}"
            if person.company:
                response += f" в {person.company}"
            response += "\n"
            
            if matches:
                response += f"   ✅ Совпадения: {', '.join(matches[:2])}\n"
            
            if person.skills:
                skills_preview = ', '.join(person.skills[:3])
                if len(person.skills) > 3:
                    skills_preview += f" и ещё {len(person.skills) - 3}"
                response += f"   🛠 Навыки: {skills_preview}\n"
            
            if person.projects:
                projects_preview = ', '.join(person.projects[:2])
                if len(person.projects) > 2:
                    projects_preview += f" и ещё {len(person.projects) - 2}"
                response += f"   🚀 Проекты: {projects_preview}\n"
            
            response += "\n"
        
        if len(matched_experts) > 5:
            response += f"📈 И ещё {len(matched_experts) - 5} экспертов...\n"
            response += "💡 Используйте /search для более детального поиска\n"
        
        # Добавляем аналитику
        response += await _generate_recommendation_analytics(matched_experts, topic)
        
        await update.message.reply_text(
            response,
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in recommend_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при поиске рекомендаций.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

async def _check_skill_synonyms(topic: str, skill: str) -> bool:
    """Проверяет синонимы навыков"""
    synonyms = {
        'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'neural networks'],
        'ml': ['machine learning', 'ai', 'deep learning'],
        'dl': ['deep learning', 'neural networks'],
        'cv': ['computer vision', 'image processing'],
        'nlp': ['natural language processing', 'text processing', 'language models'],
        'проекты': ['projects', 'work', 'experience', 'разработка', 'создание'],
        'project': ['проекты', 'работа', 'разработка'],
        'research': ['исследование', 'наука', 'академия'],
        'управление': ['management', 'leadership', 'руководство'],
        'разработка': ['development', 'engineering', 'programming'],
        'программирование': ['programming', 'coding', 'development'],
        'анализ': ['analysis', 'analytics', 'research'],
        'данные': ['data', 'analytics', 'analysis'],
        'leadership': ['управление', 'руководство', 'менеджмент'],
        'management': ['управление', 'менеджмент', 'руководство']
    }
    
    for main_topic, synonym_list in synonyms.items():
        if topic in main_topic or main_topic in topic:
            if any(synonym in skill for synonym in synonym_list):
                return True
    return False

async def _check_related_topics(topic: str, person) -> int:
    """Проверяет связанные темы"""
    related_topics = {
        'ai': ['machine learning', 'deep learning', 'neural networks', 'computer vision', 'nlp'],
        'ml': ['ai', 'deep learning', 'data science', 'statistics'],
        'programming': ['coding', 'development', 'software engineering', 'python', 'java'],
        'data': ['data science', 'analytics', 'big data', 'database'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
        'web': ['frontend', 'backend', 'fullstack', 'javascript', 'react'],
        'проекты': ['projects', 'development', 'engineering', 'product'],
        'управление': ['management', 'leadership', 'team', 'project'],
        'анализ': ['analysis', 'research', 'data', 'analytics'],
        'разработка': ['development', 'programming', 'engineering', 'coding']
    }
    
    score = 0
    for main_topic, related_list in related_topics.items():
        if topic in main_topic or main_topic in topic:
            # Проверяем навыки на связанные темы
            for skill in person.skills:
                skill_lower = skill.lower()
                if any(related in skill_lower for related in related_list):
                    score += 1
                    break
    return score

async def handle_recommend_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод темы для рекомендаций"""
    context.user_data['topic'] = update.message.text
    context.args = [update.message.text]
    return await recommend_command(update, context)

async def _show_all_experts_fallback(update: Update, topic: str, people: list):
    """Показывает всех экспертов если по теме ничего не найдено"""
    unique_people = {}
    for person in people:
        if person.name not in unique_people:
            unique_people[person.name] = person
    
    unique_list = list(unique_people.values())
    
    if len(unique_list) <= 10:
        experts_to_show = unique_list
    else:
        import random
        experts_to_show = random.sample(unique_list, 10)
    
    response = f"🔍 По теме '{topic}' точных совпадений не найдено\n\n"
    response += "💡 Вот случайные эксперты из базы:\n\n"
    
    for i, person in enumerate(experts_to_show, 1):
        response += f"{i}. {person.name}\n"
        if person.position:
            response += f"   {person.position}"
            if person.company:
                response += f" в {person.company}"
            response += "\n"
        
        if person.skills:
            skills_preview = ', '.join(person.skills[:3])
            response += f"   🛠 {skills_preview}\n"
        
        response += "\n"
    
    response += f"📊 Всего экспертов в базе: {len(unique_list)}\n\n"
    response += "💡 Советы:\n"
    response += "• Используйте /stats для статистики базы\n"
    response += "• Попробуйте другие ключевые слова\n"
    response += "• Используйте /search для расширенного поиска\n"
    response += "• Используйте /list чтобы посмотреть всех экспертов"
    
    await update.message.reply_text(
        response,
        reply_markup=get_main_keyboard()
    )

async def handle_recommend_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод темы для рекомендаций"""
    context.user_data['topic'] = update.message.text
    context.args = [update.message.text]
    return await recommend_command(update, context)

async def _generate_recommendation_analytics(matched_experts: list, topic: str) -> str:
    """Генерирует аналитику по рекомендациям"""
    if not matched_experts:
        return ""
    
    analytics = "\n🔍 Аналитика по рекомендациям:\n"
    
    companies = {}
    positions = {}
    all_skills = []
    
    for expert in matched_experts:
        person = expert['person']
        
        if person.company:
            companies[person.company] = companies.get(person.company, 0) + 1
        
        if person.position:
            positions[person.position] = positions.get(person.position, 0) + 1
        
        all_skills.extend(person.skills)
    
    if companies:
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:3]
        analytics += f"• 🏢 Топ компании: {', '.join([f'{company} ({count})' for company, count in top_companies])}\n"
    
    if positions:
        top_positions = sorted(positions.items(), key=lambda x: x[1], reverse=True)[:3]
        analytics += f"• 👔 Основные роли: {', '.join([f'{position} ({count})' for position, count in top_positions])}\n"
    
    if all_skills:
        unique_skills = len(set(all_skills))
        analytics += f"• 🛠 Уникальных навыков: {unique_skills}\n"
    
    avg_score = sum(expert['score'] for expert in matched_experts) / len(matched_experts)
    if avg_score > 2:
        relevance = "высокая"
    elif avg_score > 1:
        relevance = "средняя"
    else:
        relevance = "низкая"
    
    analytics += f"• 📊 Релевантность: {relevance} ({avg_score:.1f} баллов)\n"
    
    if avg_score < 1.5:
        analytics += f"• 💡 Совет: попробуйте более специфичные термины\n"
    
    return analytics

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    """Расширенный поиск экспертов"""
    # Если команда вызвана через кнопку, запрашиваем запрос
    if not context.args and update.message.text == '🔍 Поиск':
        await update.message.reply_text(
            "🔍 **Введите запрос для поиска:**\n\n"
            "Можно искать по:\n"
            "• Имени\n• Компании\n• Навыку\n• Должности\n• Проектам",
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
        return WAITING_SEARCH
    
    if not context.args and update.message.text != '🔍 Поиск':
        await update.message.reply_text(
            "🔍 Используйте: /search [запрос]\nИли кнопку '🔍 Поиск'",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем запрос из аргументов или текста сообщения
    if context.args:
        query = " ".join(context.args).lower().strip()
    else:
        query = update.message.text.lower().strip()
    
    try:
        await update.message.chat.send_action(action="typing")
        
        people = db.get_all_people(telegram_id)
        
        if not people:
            await update.message.reply_text(
                "❌ База данных пуста.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        # Поиск экспертов
        matched_experts = []
        seen_names = set()
        
        for person in people:
            if person.name in seen_names:
                continue
                
            score = 0
            matches = []
            
            # Поиск по имени
            if query in person.name.lower():
                score += 3
                matches.append(f"имя: {person.name}")
            
            # Поиск по должности
            if person.position and query in person.position.lower():
                score += 2
                matches.append(f"должность: {person.position}")
            
            # Поиск по компании
            if person.company and query in person.company.lower():
                score += 2
                matches.append(f"компания: {person.company}")
            
            # Поиск по навыкам
            skill_matches = []
            for skill in person.skills:
                if query in skill.lower():
                    skill_matches.append(skill)
                    score += 1
            
            if skill_matches:
                matches.append(f"навыки: {', '.join(skill_matches[:2])}")
            
            # Поиск по проектам
            project_matches = []
            for project in person.projects:
                if query in project.lower():
                    project_matches.append(project)
                    score += 1
            
            if project_matches:
                matches.append(f"проекты: {', '.join(project_matches[:2])}")
            
            if score > 0:
                matched_experts.append({
                    'person': person,
                    'score': score,
                    'matches': matches
                })
                seen_names.add(person.name)
        
        # Сортируем по релевантности
        matched_experts.sort(key=lambda x: x['score'], reverse=True)
        
        if not matched_experts:
            await update.message.reply_text(
                f"🔍 По запросу '{query}' ничего не найдено.\n\n"
                f"Попробуйте:\n"
                f"• Другие ключевые слова\n"
                f"• Более общие термины",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        # Подготавливаем данные для визуализации
        search_results_data = []
        for expert in matched_experts[:15]:
            search_results_data.append({
                'name': expert['person'].name,
                'position': expert['person'].position or 'Не указана',
                'company': expert['person'].company or 'Не указана',
                'skills': expert['person'].skills,
                'score': expert['score'],
                'matches': expert['matches']
            })
        
        # Создаем визуализации
        if search_results_data:
            try:
                # 1. График результатов поиска
                chart_html = visualizer.create_recommendations_chart(search_results_data)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(chart_html)
                    temp_file1 = f.name

                await update.message.reply_document(
                    document=open(temp_file1, 'rb'),
                    filename=f"search_results_{query}.html",
                    caption=f"📊 Результаты поиска: {query}"
                )
                os.unlink(temp_file1)
                
                # 2. Граф связей (если достаточно результатов)
                if len(search_results_data) >= 3:
                    connections = []
                    people_data_for_graph = []
                    
                    for expert in matched_experts[:8]:
                        people_data_for_graph.append({
                            'name': expert['person'].name,
                            'company': expert['person'].company or 'Не указана',
                            'skills': expert['person'].skills,
                            'position': expert['person'].position or 'Не указана'
                        })
                    
                    # Создаем связи на основе общих атрибутов
                    for i in range(len(people_data_for_graph)):
                        for j in range(i + 1, len(people_data_for_graph)):
                            # Связь по общим навыкам
                            common_skills = set(people_data_for_graph[i]['skills']) & set(people_data_for_graph[j]['skills'])
                            if common_skills:
                                connections.append((i, j))
                            # Связь по компании
                            elif (people_data_for_graph[i]['company'] == people_data_for_graph[j]['company'] and 
                                  people_data_for_graph[i]['company'] != 'Не указана'):
                                connections.append((i, j))
                            # Связь по должности
                            elif (people_data_for_graph[i]['position'] == people_data_for_graph[j]['position'] and 
                                  people_data_for_graph[i]['position'] != 'Не указана'):
                                connections.append((i, j))
                    
                    graph_html = visualizer.create_network_graph(people_data_for_graph, connections)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                        f.write(graph_html)
                        temp_file2 = f.name

                    await update.message.reply_document(
                        document=open(temp_file2, 'rb'),
                        filename=f"search_network_{query}.html",
                        caption=f"🔗 Связи найденных экспертов: {query}"
                    )
                    os.unlink(temp_file2)
                
                # 3. Тепловая карта навыков
                if any(expert['person'].skills for expert in matched_experts):
                    skills_data = []
                    for expert in matched_experts[:15]:
                        if expert['person'].skills:
                            skills_data.append({
                                'name': expert['person'].name,
                                'skills': expert['person'].skills,
                                'company': expert['person'].company or 'Не указана'
                            })
                    
                    heatmap_html = visualizer.create_skills_heatmap(skills_data)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                        f.write(heatmap_html)
                        temp_file3 = f.name

                    await update.message.reply_document(
                        document=open(temp_file3, 'rb'),
                        filename=f"search_skills_{query}.html",
                        caption=f"🎯 Навыки найденных экспертов: {query}"
                    )
                    os.unlink(temp_file3)
                
                # 4. Диаграмма компаний
                company_data = []
                for expert in matched_experts:
                    company_data.append({
                        'name': expert['person'].name,
                        'company': expert['person'].company or 'Не указана',
                        'position': expert['person'].position or 'Не указана'
                    })
                
                company_html = visualizer.create_company_distribution(company_data)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(company_html)
                    temp_file4 = f.name

                await update.message.reply_document(
                    document=open(temp_file4, 'rb'),
                    filename=f"search_companies_{query}.html",
                    caption=f"🏢 Компании найденных экспертов: {query}"
                )
                os.unlink(temp_file4)
                
            except Exception as e:
                logger.error(f"Error creating search visualizations: {e}")
                await update.message.reply_text("⚠️ Визуализации временно недоступны")
        
        # Текстовые результаты
        top_experts = matched_experts[:10]
        response = f"🔍 **Результаты поиска: '{query}'**\n\n"
        response += f"📊 Найдено экспертов: {len(matched_experts)}\n\n"
        
        for i, expert_data in enumerate(top_experts, 1):
            person = expert_data['person']
            matches = expert_data['matches']
            
            response += f"{i}. **{person.name}**\n"
            if person.position:
                response += f"   {person.position}"
                if person.company:
                    response += f" в {person.company}"
                response += "\n"
            
            # Показываем первые 2 совпадения
            if matches:
                response += f"   ✅ {matches[0]}\n"
            
            if person.skills:
                skills_preview = ', '.join(person.skills[:3])
                response += f"   🛠 {skills_preview}\n"
            
            response += "\n"
        
        if len(matched_experts) > 10:
            response += f"📈 ... и ещё {len(matched_experts) - 10} экспертов"
        
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in search_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при поиске.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает поисковый запрос"""
    context.args = [update.message.text]
    return await search_command(update, context)

async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду сравнения двух экспертов"""
    if not context.args and update.message.text == '⚖️ Сравнить':
        await update.message.reply_text(
            "⚖️ **Введите имена экспертов для сравнения:**\n\nФормат: `Имя1 vs Имя2`\nПример: `Sam Altman vs Timnit Gebru`",
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
        return WAITING_COMPARE
    
    if not context.args and update.message.text != '⚖️ Сравнить':
        await update.message.reply_text(
            "❌ Используйте: /compare [Имя1] vs [Имя2]\nИли кнопку '⚖️ Сравнить'",
            reply_markup=get_main_keyboard()
        )
        return

    try:
        if context.args:
            query = " ".join(context.args)
        else:
            query = update.message.text

        if " vs " not in query:
            await update.message.reply_text(
                "❌ Используйте 'vs' между именами",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END

        await update.message.chat.send_action(action="typing")
        
        names = query.split(" vs ")
        person_x = names[0].strip()
        person_y = names[1].strip()

        logger.info(f"🔄 Сравниваю: {person_x} vs {person_y}")

        expert_x = db.get_person_by_name(person_x)
        expert_y = db.get_person_by_name(person_y)

        if not expert_x or not expert_y:
            await update.message.reply_text(
                "❌ Один или оба эксперта не найдены в базе",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END

        # Создаем визуализацию
        person_x_data = {
            'name': expert_x.name,
            'position': expert_x.position,
            'company': expert_x.company,
            'skills': expert_x.skills,
            'projects': expert_x.projects
        }

        person_y_data = {
            'name': expert_y.name,
            'position': expert_y.position,
            'company': expert_y.company,
            'skills': expert_y.skills,
            'projects': expert_y.projects
        }

        scores = {
            'skills_score_x': len(expert_x.skills),
            'skills_score_y': len(expert_y.skills),
            'experience_score_x': 7 if "Senior" in expert_x.position else 5,
            'experience_score_y': 7 if "Senior" in expert_y.position else 5,
            'projects_score_x': len(expert_x.projects),
            'projects_score_y': len(expert_y.projects),
            'publications_score_x': 6,
            'publications_score_y': 6,
            'influence_score_x': 8 if "CEO" in expert_x.position else 5,
            'influence_score_y': 8 if "CEO" in expert_y.position else 5
        }

        chart_html = visualizer.create_people_comparison_chart(person_x_data, person_y_data, scores)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(chart_html)
            temp_file = f.name

        try:
            await update.message.reply_document(
                document=open(temp_file, 'rb'),
                filename=f"comparison_{person_x}_vs_{person_y}.html",
                caption=f"📊 Сравнение: {person_x} vs {person_y}"
            )
        finally:
            os.unlink(temp_file)

        report = f"""
⚖️ **Сравнение экспертов:**

**{person_x}**
• Должность: {expert_x.position}
• Компания: {expert_x.company}
• Навыки: {', '.join(expert_x.skills[:5])}
• Проекты: {len(expert_x.projects)}

**{person_y}**
• Должность: {expert_y.position}
• Компания: {expert_y.company}
• Навыки: {', '.join(expert_y.skills[:5])}
• Проекты: {len(expert_y.projects)}
"""
        await update.message.reply_text(
            report, 
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
            
    except Exception as e:
        logger.error(f"❌ Ошибка в compare_command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

async def handle_compare_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод для сравнения"""
    context.args = [update.message.text]
    return await compare_command(update, context)

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upload_info = """
📁 **Загрузка данных экспертов**

Бот автоматически распознает структуру ваших данных

**📊 Форматы**
• CSV/TSV
• Excel  
• JSON

**🎯 Распознавание полей**

**Имя** — name, имя, fullname
**Должность** — position, должность, title  
**Компания** — company, компания, organization
**Навыки** — skills, навыки, competencies

**🚀 Просто загрузите файл**
"""
    await update.message.reply_text(
        upload_info,
        reply_markup=get_main_keyboard()
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает загруженные файлы с анализом"""
    telegram_id = str(update.effective_user.id)
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ Файл не найден.")
        return

    # Проверяем размер файла
    if document.file_size > 10 * 1024 * 1024:
        await update.message.reply_text("❌ Файл слишком большой. Максимум 10MB.")
        return

    # Проверяем тип файла
    file_extension = document.file_name.lower().split('.')[-1]
    if file_extension not in ['csv', 'json', 'xlsx', 'xls']:
        await update.message.reply_text("❌ Поддерживаются только CSV, JSON и Excel файлы.")
        return

    try:
        await update.message.reply_text("📥 Загружаю и анализирую файл...")
        
        # Получаем содержимое файла
        file = await context.bot.get_file(document.file_id)
        file_content = await file.download_as_bytearray()
        
        # Парсим файл для конкретного пользователя
        result = await file_parser.parse_file(file_content, document.file_name, telegram_id)
        
        # Отправляем результаты
        if 'error' in result:
            await update.message.reply_text(f"❌ Ошибка: {result['error']}")
        else:
            success_message = f"""
✅ Файл успешно обработан!

📊 Результаты:
• Экспертов добавлено: {result.get('experts_added', 0)}
• Публикаций добавлено: {result.get('publications_added', 0)}
"""
            await update.message.reply_text(success_message)
            
            if 'analysis' in result and result['analysis']:
                analysis = result['analysis']
                await send_analysis_report(update, analysis)
            
            if result.get('errors'):
                errors_text = "\n".join(result['errors'][:3])
                if len(result['errors']) > 3:
                    errors_text += f"\n... и еще {len(result['errors']) - 3} ошибок"
                await update.message.reply_text(f"⚠️ Ошибки:\n{errors_text}")
            
    except Exception as e:
        logger.error(f"Error handling file for user {telegram_id}: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке файла.")

async def send_analysis_report(update: Update, analysis: dict):
    """Отправляет отчет анализа данных"""
    
    if 'insights' in analysis and analysis['insights']:
        insights_text = "🔍 **Анализ данных выявил:**\n\n" + "\n".join(f"• {insight}" for insight in analysis['insights'])
        await update.message.reply_text(insights_text, parse_mode='Markdown')
    
    if 'top_companies' in analysis and analysis['top_companies']:
        companies_text = "🏢 **Топ компаний:**\n" + "\n".join(f"• {company}: {count}" for company, count in list(analysis['top_companies'].items())[:5])
        await update.message.reply_text(companies_text)
    
    if 'top_skills' in analysis and analysis['top_skills']:
        skills_text = "🛠 **Топ навыков:**\n" + "\n".join(f"• {skill}: {count}" for skill, count in list(analysis['top_skills'].items())[:8])
        await update.message.reply_text(skills_text)
    
    if 'stats' in analysis and analysis['stats']:
        stats = analysis['stats']
        stats_text = f"""
📈 **Статистика датасета:**
• Всего экспертов: {stats.get('total_experts', 0)}
• Уникальных компаний: {stats.get('companies_count', 0)}
• Навыков на эксперта: {stats.get('avg_skills_per_expert', 0):.1f}
• Основная должность: {stats.get('most_common_position', 'N/A')}
"""
        await update.message.reply_text(stats_text, parse_mode='Markdown')

async def visualize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает визуализации базы данных"""
    telegram_id = str(update.effective_user.id)
    try:
        await update.message.chat.send_action(action="typing")
        
        people = db.get_all_people(telegram_id)
        
        if not people:
            await update.message.reply_text(
                "❌ База данных пуста.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Подготавливаем данные
        people_data = []
        for person in people:
            people_data.append({
                'name': person.name,
                'position': person.position or 'Не указана',
                'company': person.company or 'Не указана',
                'skills': person.skills,
                'projects': person.projects
            })
        
        # Создаем связи для графа
        connections = []
        for i in range(min(15, len(people_data))):
            for j in range(i + 1, min(15, len(people_data))):
                # Связь по общим навыкам
                common_skills = set(people_data[i]['skills']) & set(people_data[j]['skills'])
                if common_skills:
                    connections.append((i, j))
                # Связь по компании
                elif (people_data[i]['company'] == people_data[j]['company'] and 
                      people_data[i]['company'] != 'Не указана'):
                    connections.append((i, j))
        
        # Создаем все 4 типа визуализаций
        visualizations = [
            ("📊 График экспертов", visualizer.create_recommendations_chart(people_data[:10])),
            ("🔗 Граф связей", visualizer.create_network_graph(people_data[:15], connections)),
            ("🎯 Тепловая карта навыков", visualizer.create_skills_heatmap(people_data[:15])),
            ("🏢 Распределение по компаниям", visualizer.create_company_distribution(people_data)),
        ]
        
        sent_count = 0
        for title, chart_html in visualizations:
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(chart_html)
                    temp_file = f.name

                await update.message.reply_document(
                    document=open(temp_file, 'rb'),
                    filename=f"{title.replace(' ', '_').replace('📊', '').replace('🔗', '').replace('🎯', '').replace('🏢', '')}.html",
                    caption=title
                )
                os.unlink(temp_file)
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Error creating {title}: {e}")
                continue
        
        if sent_count > 0:
            await update.message.reply_text(
                f"✅ Отправлено {sent_count} визуализаций из 4",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось создать визуализации",
                reply_markup=get_main_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error in visualize_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при создании визуализаций.",
            reply_markup=get_main_keyboard()
        )

async def cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очищает дубликаты в базе данных"""
    telegram_id = str(update.effective_user.id)
    try:
        await update.message.reply_text("🧹 Ищу и удаляю дубликаты...")
        
        people_before = db.get_all_people(telegram_id)
        unique_before = len(set(p.name.lower().strip() for p in people_before))
        
        removed_count = db.remove_duplicates()
        
        people_after = db.get_all_people()
        unique_after = len(set(p.name.lower().strip() for p in people_after))
        
        stats_text = f"""
✅ **Очистка дубликатов завершена**

📊 **Результаты:**
• Записей до очистки: {len(people_before)}
• Записей после очистки: {len(people_after)}
• Удалено дубликатов: {removed_count}
• Уникальных экспертов: {unique_after}

💡 **Статус:** {'✅ База очищена' if removed_count == 0 else '🔄 Готово'}
"""
        await update.message.reply_text(
            stats_text, 
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in cleanup_command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при очистке дубликатов: {e}",
            reply_markup=get_main_keyboard()
        )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очищает всю базу данных"""
    try:
        stats_before = db.get_database_stats()
        people_count = stats_before.get('people_count', 0)
        
        if people_count == 0:
            await update.message.reply_text(
                "📭 База данных уже пуста!",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        confirm_keyboard = [['✅ Да, очистить базу', '❌ Нет, отмена']]
        reply_markup = ReplyKeyboardMarkup(confirm_keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            f"⚠️ **ВНИМАНИЕ: Вы собираетесь очистить всю базу данных!**\n\n"
            f"📊 **Текущая статистика:**\n"
            f"• Экспертов: {people_count}\n"
            f"• Публикаций: {stats_before.get('publications_count', 0)}\n"
            f"• Навыков: {stats_before.get('unique_skills_count', 0)}\n"
            f"• Компаний: {stats_before.get('companies_count', 0)}\n\n"
            f"❌ **Это действие нельзя отменить!**\n"
            f"Вы уверены что хотите продолжить?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        context.user_data['clear_stats'] = stats_before
        return 1
        
    except Exception as e:
        logger.error(f"Error in clear_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при подготовке очистки базы.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def confirm_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает подтверждение очистки базы"""
    user_choice = update.message.text
    
    if user_choice == '✅ Да, очистить базу':
        try:
            await update.message.reply_text(
                "🧹 Очищаю базу данных...", 
                reply_markup=ReplyKeyboardRemove()
            )
            
            stats_before = context.user_data.get('clear_stats', {})
            people_count = stats_before.get('people_count', 0)
            
            success = db.clear_database()
            
            if success:
                await update.message.reply_text(
                    f"✅ **База данных успешно очищена!**\n\n"
                    f"📊 **Удалено:**\n"
                    f"• Экспертов: {people_count}\n\n"
                    f"📁 Теперь вы можете загрузить новые данные через /upload",
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при очистке базы данных.",
                    reply_markup=get_main_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при очистке базы.",
                reply_markup=get_main_keyboard()
            )
            
    else:
        await update.message.reply_text(
            "✅ Очистка базы отменена. Данные сохранены.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

async def cancel_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет очистку базы"""
    await update.message.reply_text(
        "✅ Очистка базы отменена.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def force_cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принудительная очистка всех дубликатов"""
    telegram_id = str(update.effective_user.id)
    try:
        await update.message.reply_text("⚡ Запускаю принудительную очистку...")
        
        total_removed = 0
        iterations = 0
        
        while iterations < 10:
            removed = db.remove_duplicates()
            total_removed += removed
            iterations += 1
            
            if removed == 0:
                break
        
        people_after = db.get_all_people(telegram_id)
        unique_count = len(set(p.name.lower().strip() for p in people_after))
        
        stats_text = f"""
✅ **Принудительная очистка завершена**

📊 **Результаты:**
• Итераций очистки: {iterations}
• Всего удалено записей: {total_removed}
• Уникальных экспертов: {unique_count}
• Всего записей в базе: {len(people_after)}

💡 **Статус:** {'✅ База полностью очищена' if total_removed > 0 else '🔍 Дубликатов не найдено'}
"""
        await update.message.reply_text(
            stats_text, 
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in force_cleanup_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при принудительной очистке.",
            reply_markup=get_main_keyboard()
        )

async def handle_cleanup_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор опции очистки"""
    text = update.message.text
    
    if text == '🧹 Очистить дубликаты':
        return await cleanup_command(update, context)
    elif text == '❌ Полная очистка':
        return await clear_command(update, context)
    elif text == '❌ Отмена':
        return await cancel_command(update, context)

async def handle_visualization_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор визуализации"""
    telegram_id = str(update.effective_user.id)
    text = update.message.text
    
    if text == '📊 График рекомендаций':
        await update.message.reply_text(
            "Введите тему для графика рекомендаций:",
            reply_markup=get_cancel_keyboard()
        )
        context.user_data['visualization_type'] = 'recommendations_chart'
        return WAITING_TOPIC
    elif text == '🔗 Граф связей':
        await update.message.reply_text(
            "Введите тему для графа связей:",
            reply_markup=get_cancel_keyboard()
        )
        context.user_data['visualization_type'] = 'network_graph'
        return WAITING_TOPIC
    elif text == '🎯 Тепловая карта':
        # Создаем тепловую карту для всей базы
        try:
            await update.message.chat.send_action(action="typing")
            people = db.get_all_people(telegram_id)
            
            if not people:
                await update.message.reply_text("❌ База данных пуста.")
                return
            
            people_data = []
            for person in people[:20]:  # Ограничиваем для читаемости
                people_data.append({
                    'name': person.name,
                    'skills': person.skills,
                    'company': person.company or 'Не указана'
                })
            
            heatmap_html = visualizer.create_skills_heatmap(people_data)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(heatmap_html)
                temp_file = f.name

            await update.message.reply_document(
                document=open(temp_file, 'rb'),
                filename="skills_heatmap.html",
                caption="🎯 Тепловая карта навыков экспертов"
            )
            os.unlink(temp_file)
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            await update.message.reply_text("❌ Ошибка при создании тепловой карты")
            
    elif text == '🏢 Диаграмма компаний':
        # Создаем диаграмму компаний для всей базы
        try:
            await update.message.chat.send_action(action="typing")
            people = db.get_all_people(telegram_id)
            
            if not people:
                await update.message.reply_text("❌ База данных пуста.")
                return
            
            people_data = []
            for person in people:
                people_data.append({
                    'name': person.name,
                    'company': person.company or 'Не указана',
                    'position': person.position or 'Не указана'
                })
            
            company_html = visualizer.create_company_distribution(people_data)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(company_html)
                temp_file = f.name

            await update.message.reply_document(
                document=open(temp_file, 'rb'),
                filename="company_distribution.html",
                caption="🏢 Распределение экспертов по компаниям"
            )
            os.unlink(temp_file)
            
        except Exception as e:
            logger.error(f"Error creating company chart: {e}")
            await update.message.reply_text("❌ Ошибка при создании диаграммы компаний")
            
    elif text == '❌ Отмена':
        return await cancel_command(update, context)
    
    await update.message.reply_text(
        "Готово! Что ещё хотите сделать?",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущую операцию и возвращает в главное меню"""
    await update.message.reply_text(
        "✅ Операция отменена. Возвращаемся в главное меню.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения (нажатия кнопок)"""
    text = update.message.text
    
    if text == '🎯 Рекомендации':
        return await recommend_command(update, context)
    elif text == '🔍 Поиск':
        return await search_command(update, context)
    elif text == '⚖️ Сравнить':
        return await compare_command(update, context)
    elif text == '📊 Статистика':
        return await stats_command(update, context)
    elif text == '📁 Загрузить данные':
        return await upload_command(update, context)
    elif text == '🛠 Очистка':
        await update.message.reply_text(
            "🛠 **Выберите тип очистки:**",
            reply_markup=get_cleanup_keyboard()
        )
    elif text == '📈 Визуализации':
        await update.message.reply_text(
            "📈 **Выберите тип визуализации:**",
            reply_markup=get_visualization_keyboard()
        )
    elif text == 'ℹ️ Помощь':
        return await help_command(update, context)
    elif text == '❌ Отмена':
        return await cancel_command(update, context)
    else:
        # Если это не команда, проверяем контекст
        if 'visualization_type' in context.user_data:
            return await handle_visualization_input(update, context)
        elif text in ['🧹 Очистить дубликаты', '❌ Полная очистка']:
            return await handle_cleanup_options(update, context)
        elif text in ['📊 График рекомендаций', '🔗 Граф связей', '🎯 Тепловая карта', '🏢 Диаграмма компаний']:
            return await handle_visualization_options(update, context)
        else:
            await update.message.reply_text(
                "Не понимаю команду. Используйте кнопки меню или /help для справки.",
                reply_markup=get_main_keyboard()
            )

async def handle_visualization_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод для визуализаций"""
    visualization_type = context.user_data.get('visualization_type')
    topic = update.message.text
    
    # Очищаем контекст
    context.user_data.pop('visualization_type', None)
    
    if visualization_type in ['recommendations_chart', 'network_graph']:
        # Используем существующую логику рекомендаций для создания визуализаций
        context.args = [topic]
        return await recommend_command(update, context)
    
    await update.message.reply_text(
        "Готово!",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END
async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику пользователя"""
    telegram_id = str(update.effective_user.id)
    
    try:
        user_stats = db.get_user_stats(telegram_id)
        db_stats = db.get_database_stats(telegram_id)
        
        if not user_stats:
            await update.message.reply_text(
                "❌ Статистика не найдена.",
                reply_markup=get_main_keyboard()
            )
            return
        
        response = f"👤 Ваша статистика:\n\n"
        response += f"🆔 ID: {user_stats['user_id']}\n"
        if user_stats['username']:
            response += f"👤 Username: @{user_stats['username']}\n"
        if user_stats['first_name']:
            response += f"📛 Имя: {user_stats['first_name']}\n"
        response += f"📅 Регистрация: {user_stats['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        response += f"📊 База данных:\n"
        response += f"• Экспертов: {db_stats['people_count']}\n"
        response += f"• Публикаций: {db_stats['publications_count']}\n"
        response += f"• Навыков: {db_stats['unique_skills_count']}\n"
        response += f"• Компаний: {db_stats['companies_count']}\n\n"
        
        response += "💡 Ваши данные полностью изолированы от других пользователей"
        
        await update.message.reply_text(
            response,
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in my_stats_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении статистики.",
            reply_markup=get_main_keyboard()
        )

def setup_handlers(application):
    # Основные команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("visualize", visualize_command))
    application.add_handler(CommandHandler("cleanup", cleanup_command))
    application.add_handler(CommandHandler("force_cleanup", force_cleanup_command))
    application.add_handler(CommandHandler("mystats", my_stats_command))
    
    # ConversationHandler для рекомендаций
    recommend_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('recommend', recommend_command),
            MessageHandler(filters.Regex('^🎯 Рекомендации$'), recommend_command)
        ],
        states={
            WAITING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recommend_topic)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )
    application.add_handler(recommend_conv_handler)
    
    # ConversationHandler для поиска
    search_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('search', search_command),
            MessageHandler(filters.Regex('^🔍 Поиск$'), search_command)
        ],
        states={
            WAITING_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )
    application.add_handler(search_conv_handler)
    
    # ConversationHandler для сравнения
    compare_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('compare', compare_command),
            MessageHandler(filters.Regex('^⚖️ Сравнить$'), compare_command)
        ],
        states={
            WAITING_COMPARE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_compare_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )
    application.add_handler(compare_conv_handler)
    
    # ConversationHandler для очистки
    clear_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('clear', clear_command),
            MessageHandler(filters.Regex('^❌ Полная очистка$'), clear_command)
        ],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_clear)]
        },
        fallbacks=[CommandHandler('cancel', cancel_clear)]
    )
    application.add_handler(clear_conv_handler)
    
    # Обработчик текстовых сообщений (кнопки)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Обработчик файлов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    
    logger.info("✅ Bot handlers configured with keyboards")