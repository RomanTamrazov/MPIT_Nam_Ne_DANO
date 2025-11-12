from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ARRAY, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

# Association tables
person_projects = Table(
    'person_projects',
    Base.metadata,
    Column('person_id', Integer, ForeignKey('people.id')),
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('role', String(100))
)

person_skills = Table(
    'person_skills',
    Base.metadata,
    Column('person_id', Integer, ForeignKey('people.id')),
    Column('skill_id', Integer, ForeignKey('skills.id')),
    Column('proficiency_level', Integer)
)

class Person(Base):
    __tablename__ = 'people'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    position = Column(String(255))
    company = Column(String(255))
    social_links = Column(JSON)  # {'twitter': '', 'linkedin': '', 'github': ''}
    expertise_domains = Column(ARRAY(String))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    projects = relationship('Project', secondary=person_projects, back_populates='people')
    skills = relationship('Skill', secondary=person_skills, back_populates='people')
    publications = relationship('Publication', back_populates='person')

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    company = Column(String(255))
    technologies = Column(ARRAY(String))
    status = Column(String(50))  # 'active', 'completed', 'research'
    
    people = relationship('Person', secondary=person_projects, back_populates='projects')

class Publication(Base):
    __tablename__ = 'publications'
    
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('people.id'))
    content = Column(Text)
    source = Column(String(100))  # 'twitter', 'arxiv', 'medium'
    published_date = Column(DateTime)
    embeddings = Column(Vector(1536))  # For semantic search
    g4f_analysis = Column(JSON)  # LLM analysis results
    
    person = relationship('Person', back_populates='publications')

class Skill(Base):
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # 'ml', 'nlp', 'vision', 'infra'
    
    people = relationship('Person', secondary=person_skills, back_populates='skills')

class Connection(Base):
    __tablename__ = 'connections'
    
    id = Column(Integer, primary_key=True)
    person_a_id = Column(Integer, ForeignKey('people.id'))
    person_b_id = Column(Integer, ForeignKey('people.id'))
    connection_type = Column(String(50))  # 'COLLABORATOR', 'MENTION', 'CO_AUTHOR'
    strength = Column(Integer)  # 1-10
    evidence = Column(JSON)  # Sources proving the connection