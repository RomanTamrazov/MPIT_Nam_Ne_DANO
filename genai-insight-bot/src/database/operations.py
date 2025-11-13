from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from .models import Base, Person, Publication, User
from config.settings import settings
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def init_db(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def get_or_create_user(self, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None):
        """Получает или создает пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if not user:
                user = User(
                    telegram_id=str(telegram_id),
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info(f"Created new user: {telegram_id}")
            return user
        finally:
            session.close()
    
    def get_user_people(self, telegram_id: str):
        """Получает всех экспертов пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if user:
                return session.query(Person).filter(Person.user_id == user.id).all()
            return []
        finally:
            session.close()
    
    def add_person(self, telegram_id: str, name: str, position: str = "", company: str = "", skills: list = None, projects: list = None, social_links: dict = None):
        """Добавляет эксперта для конкретного пользователя"""
        session = self.get_session()
        try:
            user = self.get_or_create_user(telegram_id)
            person = Person(
                user_id=user.id,
                name=name,
                position=position,
                company=company,
                skills=skills or [],
                projects=projects or [],
                social_links=social_links or {}
            )
            session.add(person)
            session.commit()
            session.refresh(person)
            return person
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_person_by_name(self, telegram_id: str, name: str):
        """Находит эксперта по имени для конкретного пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if user:
                return session.query(Person).filter(
                    and_(Person.user_id == user.id, Person.name.ilike(f"%{name}%"))
                ).first()
            return None
        finally:
            session.close()
    
    def get_all_people(self, telegram_id: str):
        """Получает всех экспертов пользователя"""
        return self.get_user_people(telegram_id)
    
    def search_people_by_skill(self, telegram_id: str, skill: str):
        """Ищет экспертов по навыку для конкретного пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if not user:
                return []
            
            all_people = session.query(Person).filter(Person.user_id == user.id).all()
            return [person for person in all_people if skill and skill.lower() in [s.lower() for s in person.skills]]
        finally:
            session.close()
    
    def add_publication(self, telegram_id: str, expert_name: str, content: str, source: str = "twitter", g4f_analysis: dict = None):
        """Добавляет публикацию для конкретного пользователя"""
        session = self.get_session()
        try:
            user = self.get_or_create_user(telegram_id)
            publication = Publication(
                user_id=user.id,
                expert_name=expert_name,
                content=content,
                source=source,
                g4f_analysis=g4f_analysis or {}
            )
            session.add(publication)
            session.commit()
            return publication
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_expert_publications(self, telegram_id: str, expert_name: str):
        """Получает публикации эксперта для конкретного пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if user:
                return session.query(Publication).filter(
                    and_(Publication.user_id == user.id, Publication.expert_name.ilike(f"%{expert_name}%"))
                ).all()
            return []
        finally:
            session.close()
    
    def clear_database(self, telegram_id: str):
        """Очищает базу данных для конкретного пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if user:
                # Удаляем всех экспертов пользователя
                session.query(Person).filter(Person.user_id == user.id).delete()
                # Удаляем все публикации пользователя
                session.query(Publication).filter(Publication.user_id == user.id).delete()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing database for user {telegram_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_database_stats(self, telegram_id: str):
        """Возвращает статистику базы данных для конкретного пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if not user:
                return {
                    'people_count': 0,
                    'publications_count': 0,
                    'unique_skills_count': 0,
                    'companies_count': 0
                }
            
            people_count = session.query(Person).filter(Person.user_id == user.id).count()
            publications_count = session.query(Publication).filter(Publication.user_id == user.id).count()
            
            # Для уникальных навыков и компаний
            all_people = session.query(Person).filter(Person.user_id == user.id).all()
            
            unique_skills = set()
            companies = set()
            
            for person in all_people:
                unique_skills.update(person.skills)
                if person.company:
                    companies.add(person.company)
            
            return {
                'people_count': people_count,
                'publications_count': publications_count,
                'unique_skills_count': len(unique_skills),
                'companies_count': len(companies)
            }
        except Exception as e:
            logger.error(f"Error getting database stats for user {telegram_id}: {e}")
            return {
                'people_count': 0,
                'publications_count': 0,
                'unique_skills_count': 0,
                'companies_count': 0
            }
        finally:
            session.close()
    
    def remove_duplicates(self, telegram_id: str):
        """Удаляет дубликаты экспертов для конкретного пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if not user:
                return 0
            
            # Находим всех людей пользователя
            all_people = session.query(Person).filter(Person.user_id == user.id).all()
            
            # Создаем словарь для отслеживания уникальных имен
            unique_people = {}
            duplicates_to_remove = []
            
            for person in all_people:
                normalized_name = person.name.lower().strip()
                if normalized_name not in unique_people:
                    unique_people[normalized_name] = person
                else:
                    duplicates_to_remove.append(person)
            
            # Удаляем дубликаты
            for duplicate in duplicates_to_remove:
                session.delete(duplicate)
            
            session.commit()
            return len(duplicates_to_remove)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing duplicates for user {telegram_id}: {e}")
            return 0
        finally:
            session.close()
    
    def get_user_stats(self, telegram_id: str):
        """Получает статистику пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if user:
                people_count = session.query(Person).filter(Person.user_id == user.id).count()
                publications_count = session.query(Publication).filter(Publication.user_id == user.id).count()
                
                return {
                    'user_id': user.telegram_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'people_count': people_count,
                    'publications_count': publications_count,
                    'created_at': user.created_at
                }
            return None
        finally:
            session.close()

db = DatabaseManager()