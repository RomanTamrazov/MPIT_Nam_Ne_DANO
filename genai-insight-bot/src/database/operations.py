from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Person, Publication
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
    
    def add_person(self, name, position="", company="", skills=None, projects=None, social_links=None):
        session = self.get_session()
        try:
            person = Person(
                name=name,
                position=position,
                company=company,
                skills=skills or [],
                projects=projects or [],
                social_links=social_links or {}
            )
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
    
    def get_all_people(self):
        session = self.get_session()
        try:
            return session.query(Person).all()
        finally:
            session.close()
    
    def search_people_by_skill(self, skill):
        session = self.get_session()
        try:
            all_people = session.query(Person).all()
            return [person for person in all_people if skill and skill.lower() in [s.lower() for s in person.skills]]
        finally:
            session.close()
    
    def add_publication(self, expert_name, content, source="twitter", g4f_analysis=None):
        session = self.get_session()
        try:
            publication = Publication(
                expert_name=expert_name,
                content=content,
                source=source,
                g4f_analysis=g4f_analysis or {}
            )
            session.add(publication)
            session.commit()
            return publication
        finally:
            session.close()
    
    def get_expert_publications(self, expert_name):
        session = self.get_session()
        try:
            return session.query(Publication).filter(Publication.expert_name.ilike(f"%{expert_name}%")).all()
        finally:
            session.close()
    
    def get_recent_publications(self, limit=10):
        session = self.get_session()
        try:
            return session.query(Publication).order_by(Publication.created_at.desc()).limit(limit).all()
        finally:
            session.close()

db = DatabaseManager()