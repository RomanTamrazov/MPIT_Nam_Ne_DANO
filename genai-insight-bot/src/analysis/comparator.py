from database.operations import db
import logging

logger = logging.getLogger(__name__)

class PeopleComparator:
    def __init__(self):
        self.db = db
    
    async def compare_people(self, person_x_name: str, person_y_name: str):
        """Сравнивает двух людей"""
        person_x = self.db.get_person_by_name(person_x_name)
        person_y = self.db.get_person_by_name(person_y_name)
        
        if not person_x:
            return {'error': f'Эксперт "{person_x_name}" не найден'}
        if not person_y:
            return {'error': f'Эксперт "{person_y_name}" не найден'}
        
        return {
            'person_x': person_x,
            'person_y': person_y,
            'comparison': self._generate_comparison_insights(person_x, person_y)
        }
    
    async def generate_comparison_report(self, person_x_name: str, person_y_name: str) -> str:
        """Генерирует отчет сравнения"""
        result = await self.compare_people(person_x_name, person_y_name)
        
        if 'error' in result:
            return f"❌ {result['error']}"
        
        person_x = result['person_x']
        person_y = result['person_y']
        
        # Форматируем навыки и проекты
        x_skills = ', '.join(person_x.skills) if person_x.skills else 'не указаны'
        y_skills = ', '.join(person_y.skills) if person_y.skills else 'не указаны'
        x_projects = ', '.join(person_x.projects) if person_x.projects else 'не указаны'
        y_projects = ', '.join(person_y.projects) if person_y.projects else 'не указаны'
        
        report = f"""
🆚 **СРАВНЕНИЕ: {person_x.name} vs {person_y.name}**

🏢 **Компании:**
• {person_x.name}: {person_x.company or 'Не указана'}
• {person_y.name}: {person_y.company or 'Не указана'}

👔 **Должности:**
• {person_x.name}: {person_x.position or 'Не указана'}
• {person_y.name}: {person_y.position or 'Не указана'}

🛠 **Навыки:**
• {person_x.name}: {x_skills}
• {person_y.name}: {y_skills}

🚀 **Проекты:**
• {person_x.name}: {x_projects}
• {person_y.name}: {y_projects}

{result['comparison']}
"""
        return report
    
    def _generate_comparison_insights(self, person_x, person_y):
        """Генерирует инсайты сравнения"""
        insights = []
        
        # Сравнение навыков
        x_skills = set(person_x.skills) if person_x.skills else set()
        y_skills = set(person_y.skills) if person_y.skills else set()
        
        common_skills = x_skills.intersection(y_skills)
        unique_x_skills = x_skills - y_skills
        unique_y_skills = y_skills - x_skills
        
        if common_skills:
            insights.append(f"🤝 **Общие навыки:** {', '.join(list(common_skills)[:3])}")
        
        if unique_x_skills:
            insights.append(f"⭐ **Уникальные навыки {person_x.name}:** {', '.join(list(unique_x_skills)[:2])}")
        
        if unique_y_skills:
            insights.append(f"⭐ **Уникальные навыки {person_y.name}:** {', '.join(list(unique_y_skills)[:2])}")
        
        # Сравнение компаний
        if person_x.company and person_y.company:
            if person_x.company == person_y.company:
                insights.append(f"🏢 Оба работают в **{person_x.company}**")
            else:
                insights.append("🏢 Работают в разных компаниях")
        
        # Сравнение опыта (на основе количества проектов)
        x_projects_count = len(person_x.projects) if person_x.projects else 0
        y_projects_count = len(person_y.projects) if person_y.projects else 0
        
        if x_projects_count > y_projects_count:
            insights.append(f"📊 **{person_x.name}** имеет больше проектов ({x_projects_count} vs {y_projects_count})")
        elif y_projects_count > x_projects_count:
            insights.append(f"📊 **{person_y.name}** имеет больше проектов ({y_projects_count} vs {x_projects_count})")
        else:
            insights.append("📊 Оба имеют одинаковое количество проектов")
        
        return "\n".join(insights) if insights else "💡 Эксперты имеют разные профили компетенций"

comparator = PeopleComparator()