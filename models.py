from sqlalchemy import Column, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

Base = declarative_base()

# Define the desired tables as below, or use sqlalchemy autofind to
# automatically define the classes based on the imported OSM tables?


class OSMPoint(Base):
    __tablename__ = 'osmpoints'
    node_id = Column(BigInteger, primary_key=True)
    tags = Column(JSONB)
    geom = Column(Geometry)


class OSMPolygon(Base):
    __tablename__ = 'osmpolygons'
    area_id = Column(BigInteger, primary_key=True)
    tags = Column(JSONB)
    geom = Column(Geometry)


# Use JSONB field for all datasets so we won't need migrations in the future

class FlickrPoint(Base):
    __tablename__ = 'flickrpoints'
    point_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry)


class GTFSStop(Base):
    __tablename__ = 'gtfsstops'
    stop_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry)


# We usually have a completely different (denser) dataset of nodes for local
# accessibility. Makes no sense to save them in the same table as the OSM POIs.

class OSMAccessNode(Base):
    __tablename__ = 'osmaccessnodes'
    node_id = Column(BigInteger, primary_key=True)
    accessibilities = Column(JSONB)
    geom = Column(Geometry)
