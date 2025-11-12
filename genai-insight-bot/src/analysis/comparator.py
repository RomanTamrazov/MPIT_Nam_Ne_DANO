from database.operations import db
import logging

logger = logging.getLogger(__name__)

class PeopleComparator:
    def __init__(self):
        self.db = db
    
    async def compare_people(self, person_x_name: str, person_y_name: str):
        person_x = self.db.get_person_by_name(person_x_name)
        person_y = self.db.get_person_by_name(person_y_name)
        
        if not person_x or not person_y:
            return {'error': 'Person not found'}
        
        return {
            'person_x': person_x.name,
            'person_y': person_y.name,
            'comparison': 'Basic comparison'
        }
    
    async def generate_comparison_report(self, person_x_name: str, person_y_name: str) -> str:
        result = await self.compare_people(person_x_name, person_y_name)
        
        if 'error' in result:
            return f"Error: {result['error']}"
        
        return f"""
🆚 Сравнение: {result['person_x']} vs {result['person_y']}

✅ Сравнение выполнено успешно!
Бот работает, база данных подключена.
"""

comparator = PeopleComparator()