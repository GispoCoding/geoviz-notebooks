import datetime
from sqlalchemy import Column, BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.sql import expression, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

Base = declarative_base()


# Here we store the current and past import runs
class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    # By default, populate the slug from the city name. Still, future proof
    # the DB just in case we start having multiple analyses with multiple
    # slugs for the same city, or analyses/cities with identical names.
    name = Column(String, nullable=False)
    bbox = Column(Geometry(geometry_type='POLYGON'))
    # Future-proof the datasets field too. We might get more datasets, we
    # don't want to have to do migrations to the analysis table in that case.
    datasets = Column(JSONB)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.now, server_default=func.now())
    finish_time = Column(DateTime)
    # set this field True once the user has seen the result
    viewed = Column(Boolean, nullable=False, default=False, server_default=expression.false())


# Define the desired tables as below, or use sqlalchemy autofind to
# automatically define the classes based on the imported OSM tables?


class OSMPoint(Base):
    __tablename__ = 'osmpoints'
    node_id = Column(BigInteger, primary_key=True)
    tags = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT'))


class OSMPolygon(Base):
    __tablename__ = 'osmpolygons'
    area_id = Column(BigInteger, primary_key=True)
    tags = Column(JSONB)
    geom = Column(Geometry(geometry_type='POLYGON'))


# Use JSONB field for all datasets so we won't need migrations in the future

class FlickrPoint(Base):
    __tablename__ = 'flickrpoints'
    point_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT'))


class GTFSStop(Base):
    __tablename__ = 'gtfsstops'
    stop_id = Column(String, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT'))


# We usually have a completely different (denser) dataset of nodes for local
# accessibility. Makes no sense to save them in the same table as the OSM POIs.

class OSMAccessNode(Base):
    __tablename__ = 'osmaccessnodes'
    node_id = Column(BigInteger, primary_key=True)
    accessibilities = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT'))


class OoklaPoint(Base):
    __tablename__ = 'ooklapoints'
    quadkey_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT'))


class KonturPoint(Base):
    __tablename__ = 'konturpoints'
    hex_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT'))
