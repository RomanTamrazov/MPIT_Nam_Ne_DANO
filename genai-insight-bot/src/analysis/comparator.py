from typing import Dict, List, Any
from database.operations import db
from .g4f_analyzer import analyzer
import asyncio

class PeopleComparator:
    def __init__(self):
        self.db = db
    
    async def compare_people(self, person_x_name: str, person_y_name: str) -> Dict[str, Any]:
        """Compare two people using G4F analysis"""
        
        # Get people data
        person_x = self.db.get_person_by_name(person_x_name)
        person_y = self.db.get_person_by_name(person_y_name)
        
        if not person_x or not person_y:
            return {'error': 'One or both people not found'}
        
        # Prepare comparison data
        comparison_data = self._prepare_comparison_data(person_x, person_y)
        
        # Analyze with G4F
        analysis = await analyzer.analyze_text(
            str(comparison_data), 
            'comparison_analysis'
        )
        
        # Enhance with database insights
        enhanced_analysis = self._enhance_with_db_insights(analysis, person_x, person_y)
        
        return enhanced_analysis
    
    def _prepare_comparison_data(self, person_x, person_y) -> Dict[str, Any]:
        """Prepare structured data for comparison"""
        
        return {
            'person_x': {
                'name': person_x.name,
                'position': person_x.position,
                'company': person_x.company,
                'expertise_domains': person_x.expertise_domains or [],
                'skills': [skill.name for skill in person_x.skills],
                'recent_projects': [project.name for project in person_x.projects[:3]]
            },
            'person_y': {
                'name': person_y.name,
                'position': person_y.position,
                'company': person_y.company,
                'expertise_domains': person_y.expertise_domains or [],
                'skills': [skill.name for skill in person_y.skills],
                'recent_projects': [project.name for project in person_y.projects[:3]]
            },
            'comparison_context': {
                'metrics': ['technical_expertise', 'industry_influence', 'innovation', 'communication_style'],
                'scale': '1-10'
            }
        }
    
    def _enhance_with_db_insights(self, analysis: Dict, person_x, person_y) -> Dict[str, Any]:
        """Add database-driven insights to G4F analysis"""
        
        # Get connections strength
        x_connections = len(self.db.get_people_connections(person_x.id))
        y_connections = len(self.db.get_people_connections(person_y.id))
        
        # Get recent activity
        x_publications = self.db.get_recent_publications(person_x.id, 5)
        y_publications = self.db.get_recent_publications(person_y.id, 5)
        
        enhanced = analysis.copy()
        enhanced['database_insights'] = {
            'network_size': {
                person_x.name: x_connections,
                person_y.name: y_connections
            },
            'recent_activity': {
                person_x.name: len(x_publications),
                person_y.name: len(y_publications)
            },
            'common_connections': self._find_common_connections(person_x.id, person_y.id),
            'collaboration_potential': self._calculate_collaboration_potential(person_x, person_y)
        }
        
        return enhanced
    
    def _find_common_connections(self, person_x_id: int, person_y_id: int) -> List[str]:
        """Find people who are connected to both persons"""
        x_connections = {conn[0] for conn in self.db.get_people_connections(person_x_id)}
        y_connections = {conn[0] for conn in self.db.get_people_connections(person_y_id)}
        common = x_connections.intersection(y_connections)
        return list(common)
    
    def _calculate_collaboration_potential(self, person_x, person_y) -> Dict[str, Any]:
        """Calculate potential for collaboration"""
        
        x_skills = {skill.name for skill in person_x.skills}
        y_skills = {skill.name for skill in person_y.skills}
        common_skills = x_skills.intersection(y_skills)
        complementary_skills = x_skills.symmetric_difference(y_skills)
        
        return {
            'skill_overlap': len(common_skills),
            'complementary_skills': len(complementary_skills),
            'potential_synergy': min(10, len(common_skills) + len(complementary_skills) // 2),
            'recommended_collaboration_areas': list(complementary_skills)[:3]
        }
    
    async def generate_comparison_report(self, person_x_name: str, person_y_name: str) -> str:
        """Generate human-readable comparison report"""
        
        analysis = await self.compare_people(person_x_name, person_y_name)
        
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        report = f"""
🆚 **СРАВНИТЕЛЬНЫЙ АНАЛИЗ: {person_x_name} vs {person_y_name}**

🏆 **Сферы экспертизы:**
• {person_x_name}: {', '.join(analysis.get('person_x', {}).get('expertise_domains', []))}
• {person_y_name}: {', '.join(analysis.get('person_y', {}).get('expertise_domains', []))}

💡 **Ключевые различия:**
{self._format_differences(analysis.get('key_differences', []))}

🤝 **Потенциальные точки коллаборации:**
{chr(10).join(f'• {area}' for area in analysis.get('database_insights', {}).get('collaboration_potential', {}).get('recommended_collaboration_areas', []))}

📊 **Сетевая активность:**
• {person_x_name}: {analysis.get('database_insights', {}).get('network_size', {}).get(person_x_name, 0)} связей
• {person_y_name}: {analysis.get('database_insights', {}).get('network_size', {}).get(person_y_name, 0)} связей

🎯 **Рекомендации:**
{chr(10).join(f'• {rec}' for rec in analysis.get('recommendations', []))}
        """
        
        return report
    
    def _format_differences(self, differences: List[str]) -> str:
        return chr(10).join(f'• {diff}' for diff in differences)

# Global comparator instance
comparator = PeopleComparator()