from typing import Dict, List, Any, Optional
from database.operations import db
from .g4f_analyzer import analyzer
import asyncio
from collections import defaultdict

class ExpertRecommender:
    def __init__(self):
        self.db = db
    
    async def recommend_experts(self, topic: str, max_recommendations: int = 5) -> Dict[str, Any]:
        """Recommend experts for a specific topic"""
        
        # First, analyze the topic
        topic_analysis = await analyzer.analyze_text(topic, 'skill_extraction')
        
        # Find relevant people from database
        relevant_people = self._find_relevant_people(topic, topic_analysis)
        
        if not relevant_people:
            return {'error': 'No experts found for this topic'}
        
        # Score and rank people
        ranked_experts = await self._score_and_rank_experts(relevant_people, topic, topic_analysis)
        
        # Generate detailed recommendations
        recommendations = await self._generate_detailed_recommendations(
            ranked_experts[:max_recommendations], 
            topic
        )
        
        return {
            'topic': topic,
            'topic_analysis': topic_analysis,
            'recommendations': recommendations,
            'total_experts_found': len(ranked_experts)
        }
    
    def _find_relevant_people(self, topic: str, topic_analysis: Dict) -> List[Any]:
        """Find people relevant to the topic using multiple strategies"""
        
        relevant_people = set()
        
        # Strategy 1: Search by skills
        skills_to_search = topic_analysis.get('technical_skills', []) + topic_analysis.get('domains', [])
        for skill in skills_to_search[:3]:  # Use top 3 skills
            people_with_skill = self.db.search_people_by_skill(skill)
            relevant_people.update(people_with_skill)
        
        # Strategy 2: Search in expertise domains
        session = self.db.get_session()
        try:
            people_by_domain = session.query(db.Person).filter(
                db.Person.expertise_domains.contains([topic])
            ).all()
            relevant_people.update(people_by_domain)
        finally:
            session.close()
        
        # Strategy 3: Search in publications content
        session = self.db.get_session()
        try:
            query = text("""
                SELECT DISTINCT p.* 
                FROM people p
                JOIN publications pub ON p.id = pub.person_id
                WHERE pub.content ILIKE :topic
                OR pub.g4f_analysis::text ILIKE :topic
            """)
            people_by_publications = session.execute(query, {'topic': f'%{topic}%'}).fetchall()
            relevant_people.update([row[0] for row in people_by_publications])
        finally:
            session.close()
        
        return list(relevant_people)
    
    async def _score_and_rank_experts(self, people: List, topic: str, topic_analysis: Dict) -> List[Dict]:
        """Score and rank experts by relevance"""
        
        scored_experts = []
        
        for person in people:
            score = await self._calculate_expert_score(person, topic, topic_analysis)
            scored_experts.append({
                'person': person,
                'score': score,
                'relevance_breakdown': score['breakdown']
            })
        
        # Sort by total score
        scored_experts.sort(key=lambda x: x['score']['total'], reverse=True)
        return scored_experts
    
    async def _calculate_expert_score(self, person, topic: str, topic_analysis: Dict) -> Dict[str, float]:
        """Calculate comprehensive expert score"""
        
        scores = {
            'skill_match': 0.0,
            'domain_expertise': 0.0,
            'recent_activity': 0.0,
            'influence': 0.0,
            'innovation': 0.0
        }
        
        # Skill match score
        person_skills = {skill.name.lower() for skill in person.skills}
        topic_skills = {skill.lower() for skill in topic_analysis.get('technical_skills', [])}
        skill_overlap = len(person_skills.intersection(topic_skills))
        scores['skill_match'] = min(10, skill_overlap * 2)
        
        # Domain expertise score
        person_domains = {domain.lower() for domain in (person.expertise_domains or [])}
        topic_domains = {domain.lower() for domain in topic_analysis.get('domains', [])}
        domain_overlap = len(person_domains.intersection(topic_domains))
        scores['domain_expertise'] = min(10, domain_overlap * 3)
        
        # Recent activity score
        recent_pubs = self.db.get_recent_publications(person.id, 6)  # Last 6 months
        scores['recent_activity'] = min(10, len(recent_pubs) * 2)
        
        # Influence score (based on connections)
        connections = self.db.get_people_connections(person.id)
        scores['influence'] = min(10, len(connections) * 0.5)
        
        # Innovation score (based on unique projects and skills)
        unique_skills = len(person_skills)
        unique_projects = len(person.projects)
        scores['innovation'] = min(10, (unique_skills + unique_projects) * 0.3)
        
        # Calculate total score (weighted)
        weights = {
            'skill_match': 0.3,
            'domain_expertise': 0.25,
            'recent_activity': 0.2,
            'influence': 0.15,
            'innovation': 0.1
        }
        
        total_score = sum(scores[key] * weights[key] for key in scores)
        
        return {
            'total': total_score,
            'breakdown': scores,
            'weighted_total': total_score
        }
    
    async def _generate_detailed_recommendations(self, experts: List[Dict], topic: str) -> List[Dict[str, Any]]:
        """Generate detailed recommendation objects"""
        
        recommendations = []
        
        for expert_data in experts:
            person = expert_data['person']
            score = expert_data['score']
            
            # Get recent publications for context
            recent_pubs = self.db.get_recent_publications(person.id, 3)
            
            # Generate AI-powered justification
            justification = await self._generate_recommendation_justification(person, topic, recent_pubs)
            
            recommendation = {
                'rank': len(recommendations) + 1,
                'name': person.name,
                'position': person.position,
                'company': person.company,
                'relevance_score': score['total'],
                'score_breakdown': score['breakdown'],
                'key_skills': [skill.name for skill in person.skills][:5],
                'recent_work': [project.name for project in person.projects][:3],
                'justification': justification,
                'social_links': person.social_links or {},
                'why_follow': self._generate_why_follow(person, topic)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_recommendation_justification(self, person, topic: str, recent_pubs: List) -> str:
        """Generate AI-powered justification for recommendation"""
        
        context = f"""
        Эксперт: {person.name}
        Должность: {person.position}
        Компания: {person.company}
        Навыки: {', '.join([skill.name for skill in person.skills][:5])}
        Проекты: {', '.join([project.name for project in person.projects][:3])}
        Тема рекомендации: {topic}
        """
        
        prompt = f"""
        Объясни, почему {person.name} является экспертом в теме "{topic}". 
        Используй информацию ниже и верни ОДИН абзац на русском:
        
        {context}
        
        Ответ должен быть кратким, убедительным и содержать конкретные причины.
        """
        
        try:
            response = await analyzer.analyze_text(prompt, 'default_analysis')
            return response.get('summary', f'{person.name} имеет релевантный опыт в области {topic}.')
        except:
            return f'{person.name} обладает значительным опытом в области {topic}.'
    
    def _generate_why_follow(self, person, topic: str) -> List[str]:
        """Generate reasons why this expert is worth following"""
        
        reasons = []
        
        if len(person.projects) > 2:
            reasons.append(f"Активно работает над проектами в области {topic}")
        
        if len(person.skills) > 5:
            reasons.append("Обладает разнообразным техническим бэкграундом")
        
        connections = self.db.get_people_connections(person.id)
        if len(connections) > 10:
            reasons.append("Сильно связан с другими экспертами индустрии")
        
        recent_pubs = self.db.get_recent_publications(person.id, 3)
        if recent_pubs:
            reasons.append("Регулярно делится инсайтами и публикациями")
        
        # Default reasons
        if not reasons:
            reasons = [
                f"Специализируется на {topic}",
                "Имеет практический опыт в релевантных проектах",
                "Активен в профессиональном сообществе"
            ]
        
        return reasons[:3]
    
    async def get_recommendation_report(self, topic: str, max_recommendations: int = 5) -> str:
        """Generate human-readable recommendation report"""
        
        result = await self.recommend_experts(topic, max_recommendations)
        
        if 'error' in result:
            return f"❌ {result['error']}"
        
        report = f"""
🔍 **РЕКОМЕНДАЦИИ ЭКСПЕРТОВ ПО ТЕМЕ: {topic.upper()}**

📊 Найдено экспертов: {result['total_experts_found']}
🎯 Топ-{len(result['recommendations'])} рекомендаций:

"""
        
        for i, rec in enumerate(result['recommendations'], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
            
            report += f"""
{medal} **{rec['name']}** - {rec['position']} @ {rec['company']}
   • Релевантность: {rec['relevance_score']:.1f}/10
   • Ключевые навыки: {', '.join(rec['key_skills'][:3])}
   • Почему следить: {rec['why_follow'][0]}
   • Обоснование: {rec['justification']}
"""
        
        return report

# Global recommender instance
recommender = ExpertRecommender()