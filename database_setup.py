import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Setup Course Table
class Course(Base):
    __tablename__ = 'course'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category = Column(String(250))
    picture_name = Column(String(250))
    user_id = Column(Integer, ForeignKey('users.id'))

# Setup CourseItem Table
class CourseItem(Base):
    __tablename__ = 'course_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category = Column(String(250))
    youtube_url = Column(String(250))
    audio_url = Column(String(250))
    text = Column(String(250))
    course_id = Column(Integer, ForeignKey('course.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    course = relationship(Course)

    # Setup API Endpoints
    @property
    def serialize(self):
        return{
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'course_id': self.course_id,
            'category': self.category,
            'youtube_url': self.youtube_url,
            'audio_url': self.audio_url,
            'text': self.text,
            'user_id': self.user_id
        }

# Setup User Table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(200))
    profile_pic = Column(String(250))
    github_access_token = Column(String(200))
    
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL','postgresql://James:james@localhost:5432/mytest')
engine = create_engine(SQLALCHEMY_DATABASE_URI)

Base.metadata.create_all(engine)