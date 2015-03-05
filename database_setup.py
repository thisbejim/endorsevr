import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Course(Base):
    __tablename__ = 'course'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category = Column(String(250))
    timezone = Column(String(80))
    max_students = Column(Integer)


class CourseItem(Base):
    __tablename__ = 'course_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category = Column(String(250))
    youtube_url = Column(String(250))
    audio_url = Column(String(250))
    text = Column(String(250))
    #position = Column(Integer) the position in the course flow
    course_id = Column(Integer, ForeignKey('course.id'))
    course = relationship(Course)

class Student(Base):
    __tablename__ = 'student'
    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('course.id'))
    course = relationship(Course)

#class user

    @property
    def serialize(self):
        return{
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'course': self.course,
        }

engine = create_engine('sqlite:///mentor.db')

Base.metadata.create_all(engine)