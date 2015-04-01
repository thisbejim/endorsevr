import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Setup Project Table
class Project(Base):
    __tablename__ = 'project'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    tag_line = Column(String(250))
    category = Column(String(250))
    picture_name = Column(String(250))
    user_id = Column(Integer, ForeignKey('users.id'))
    youtube_url = Column(String(250))
    time_created = Column(DateTime)
    approved = Column(Boolean, unique=False, default=False)

# Setup Asset Table
class Asset(Base):
    __tablename__ = 'asset'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    tag_line = Column(String(250))
    category = Column(String(250))
    sub_category = Column(String(250))
    picture_name = Column(String(250))
    user_id = Column(Integer, ForeignKey('users.id'))
    project_id = Column(Integer, ForeignKey('project.id'))
    model_url = Column(String(250))
    dimensions = Column(String(250))
    price = Column(Float(scale=2))
    time_created = Column(DateTime)


class Paragraph(Base):
    __tablename__ = 'paragraph'
    id = Column(Integer, primary_key=True)
    text = Column(String(2000))
    project_id = Column(Integer, ForeignKey('project.id'))
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
    advertiser = Column(Boolean, unique=False, default=False)
    stripe_user_id = Column(String(200))
    stripe_publishable_key = Column(String(200))
    access_token = Column(String(200))

# Setup Endorsement Table
class Endorsement(Base):
    __tablename__ = 'endorsement'
    id = Column(Integer, primary_key=True)
    advertiser_id = Column(Integer)
    advertiser_username = Column(String(200))
    creator_id = Column(Integer)
    creator_username = Column(String(200))
    asset_id = Column(Integer)
    asset_name = Column(String(200))
    asset_picture = Column(String(200))
    texture_file = Column(String(200))
    active = Column(Boolean, unique=False, default=True)
    time_created = Column(DateTime)
    
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL','postgresql://James:james@localhost:5432/mytest')
engine = create_engine(SQLALCHEMY_DATABASE_URI)

Base.metadata.create_all(engine)