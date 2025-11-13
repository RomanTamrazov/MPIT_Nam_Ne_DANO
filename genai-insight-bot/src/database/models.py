from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с экспертами и публикациями
    people = relationship("Person", back_populates="user", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="user", cascade="all, delete-orphan")

class Person(Base):
    __tablename__ = 'people'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    position = Column(String(200))
    company = Column(String(200))
    skills = Column(JSON, default=list)  # Список навыков
    projects = Column(JSON, default=list)  # Список проектов
    social_links = Column(JSON, default=dict)  # Соцсети
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="people")

class Publication(Base):
    __tablename__ = 'publications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    expert_name = Column(String(200), nullable=False)
    content = Column(Text)
    source = Column(String(100))
    g4f_analysis = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="publications")