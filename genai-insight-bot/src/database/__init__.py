"""
Database module for data storage and operations
"""

from .models import Base, Person, Project, Publication, Skill, Connection
from .operations import DatabaseManager, db

__all__ = ['Base', 'Person', 'Project', 'Publication', 'Skill', 'Connection', 'DatabaseManager', 'db']