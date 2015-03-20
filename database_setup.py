import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Setup Course Table
class Asset(Base):
    __tablename__ = 'asset'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    tag_line = Column(String(250))
    description = Column(String(2000))
    category = Column(String(250))
    sub_category = Column(String(250))
    picture_name = Column(String(250))
    user_id = Column(Integer, ForeignKey('users.id'))
    youtube_url = Column(String(250))
    dimensions = Column(String(250))
    price = Column(Float(scale=2))
    time_created = Column(DateTime)

# Setup User Table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(200))
    email = Column(String(200))
    password_hash = Column(String(200))
    website = Column(String(200))
    profile_pic = Column(String(250))
    github_id = Column(String(200))
    twitter_id = Column(String(200))
    facebook_id = Column(String(200))

class Endorsement(Base):
    __tablename__ = 'endorsement'
    id = Column(Integer, primary_key=True)
    advertiser_id = Column(Integer)
    advertiser_username = Column(String(200))
    creator_id = Column(Integer)
    creator_username = Column(String(200))
    texture_file = Column(String(200))
    
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL','postgresql://James:james@localhost:5432/mytest')
engine = create_engine(SQLALCHEMY_DATABASE_URI)

Base.metadata.create_all(engine)