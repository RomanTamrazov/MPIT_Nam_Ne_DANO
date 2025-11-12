from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Person(Base):
    __tablename__ = 'people'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    position = Column(String(255))
    company = Column(String(255))
    skills = Column(JSON)
    projects = Column(JSON)
    social_links = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class Publication(Base):
    __tablename__ = 'publications'
    
    id = Column(Integer, primary_key=True)
    expert_name = Column(String(255))
    content = Column(Text)
    source = Column(String(100))
    g4f_analysis = Column(JSON)
    created_at = Column(DateTime, default=func.now())