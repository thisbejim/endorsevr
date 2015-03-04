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


class CourseItem(Base):
    __tablename__ = 'course_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category = Column(String(250))
    price = Column(String(8))
    course_id = Column(Integer, ForeignKey('course.id'))
    course = relationship(Course)

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