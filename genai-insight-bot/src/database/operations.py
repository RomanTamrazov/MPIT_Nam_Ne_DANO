from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base, Person, Project, Publication, Skill, Connection
from config.settings import settings
import json

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def init_db(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    # Person operations
    def add_person(self, person_data):
        session = self.get_session()
        try:
            person = Person(**person_data)
            session.add(person)
            session.commit()
            return person
        finally:
            session.close()
    
    def get_person_by_name(self, name):
        session = self.get_session()
        try:
            return session.query(Person).filter(Person.name.ilike(f"%{name}%")).first()
        finally:
            session.close()
    
    def search_people_by_skill(self, skill):
        session = self.get_session()
        try:
            return session.query(Person).join(Person.skills).filter(Skill.name.ilike(f"%{skill}%")).all()
        finally:
            session.close()
    
    # Publication operations
    def add_publication(self, publication_data):
        session = self.get_session()
        try:
            publication = Publication(**publication_data)
            session.add(publication)
            session.commit()
            return publication
        finally:
            session.close()
    
    def get_recent_publications(self, limit=10):
        session = self.get_session()
        try:
            return session.query(Publication).order_by(Publication.published_date.desc()).limit(limit).all()
        finally:
            session.close()
    
    # Analysis operations
    def get_people_connections(self, person_id):
        session = self.get_session()
        try:
            query = text("""
                SELECT p2.name, c.connection_type, c.strength 
                FROM connections c
                JOIN people p1 ON c.person_a_id = p1.id
                JOIN people p2 ON c.person_b_id = p2.id
                WHERE p1.id = :person_id
                ORDER BY c.strength DESC
            """)
            return session.execute(query, {'person_id': person_id}).fetchall()
        finally:
            session.close()
    
    def find_similar_people(self, person_id, limit=5):
        """Find people with similar skills and projects"""
        session = self.get_session()
        try:
            query = text("""
                SELECT p2.id, p2.name, p2.position, 
                       COUNT(DISTINCT ps.skill_id) as common_skills,
                       COUNT(DISTINCT pp.project_id) as common_projects
                FROM people p1
                JOIN people p2 ON p1.id != p2.id
                LEFT JOIN person_skills ps1 ON p1.id = ps1.person_id
                LEFT JOIN person_skills ps2 ON p2.id = ps2.person_id AND ps1.skill_id = ps2.skill_id
                LEFT JOIN person_projects pp1 ON p1.id = pp1.person_id
                LEFT JOIN person_projects pp2 ON p2.id = pp2.person_id AND pp1.project_id = pp2.project_id
                WHERE p1.id = :person_id
                GROUP BY p2.id, p2.name, p2.position
                ORDER BY (common_skills + common_projects) DESC
                LIMIT :limit
            """)
            return session.execute(query, {'person_id': person_id, 'limit': limit}).fetchall()
        finally:
            session.close()

# Global database instance
db = DatabaseManager()