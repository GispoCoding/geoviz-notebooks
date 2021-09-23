from sqlalchemy import Column, BigInteger, ForeignKey, Integer, String
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
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
    populations_200 = Column(JSONB)
    populations_400 = Column(JSONB)


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


class PopulationHex(Base):
    __tablename__ = 'populationhexes'
    hex_id = Column(String, primary_key=True)
    # for performance, we cannot use json here
    total = Column(Integer)
    children_under_five = Column(Integer)
    elderly_60_plus = Column(Integer)
    men = Column(Integer)
    women = Column(Integer)
    women_of_reproductive_age_15_49 = Column(Integer)
    youth_15_24 = Column(Integer)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))


class GooglePoint(Base):
    __tablename__ = 'googlepoints'
    node_id = Column(String, primary_key=True)
    osm_node_id = Column(BigInteger, ForeignKey('osmpoints.node_id'), index=True)
    popularity = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
