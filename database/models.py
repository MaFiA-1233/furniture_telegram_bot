from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.engine import Base
from uuid import uuid4
import datetime


class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    firstname = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    registration_date = Column(DateTime, default=datetime.datetime.now)
    is_admin = Column(Boolean, default=False, nullable=False)


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<Category(id={self.id}, name="{self.name}")>'


class Furniture(Base):
    __tablename__ = 'furniture'   

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=True)
    category_name = Column(String, ForeignKey('categories.name'), nullable=False)
    kitchen_type = Column(String, nullable=True)
    country_origin = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    photos = relationship('FurniturePhoto', back_populates='furniture', cascade='all, delete-orphan')


class FurniturePhoto(Base):
    __tablename__ = 'furniture_photos'

    id = Column(Integer, primary_key=True, index=True)
    furniture_id = Column(Integer, ForeignKey('furniture.id'), nullable=False)
    file_id = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now) 

    furniture = relationship('Furniture', back_populates='photos')

    