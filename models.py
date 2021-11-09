import datetime
from sqlalchemy import Column, BigInteger, Boolean, DateTime, Index, Integer, String
from sqlalchemy.sql import expression, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
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
    datasets = Column(JSONB)  # mark datasets like {selected: ['osm', 'flickr'], imported: ['osm']}
    parameters = Column(JSONB)  # mark params like {gtfs: {url: http://example.com}}
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.now(), server_default=func.now())
    finish_time = Column(DateTime)
    # set this field True once the user has seen the result
    viewed = Column(Boolean, nullable=False, default=False, server_default=expression.false())


# This is for data in slug-specific schemas
class SchemaBase(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (
            # geoalchemy doesn't use schema_translate_map if autocreating index
            # https://github.com/geoalchemy/geoalchemy2/issues/137
            # so we have to declare the index manually instead
            Index(f'idx_{cls.__tablename__}_geom', 'geom', postgresql_using='gist'),
            # needed for schema_translate_map
            {'schema': 'schema'}
        )


class OSMPoint(SchemaBase):
    __tablename__ = 'osmpoints'
    node_id = Column(BigInteger, primary_key=True)
    tags = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', spatial_index=False))


class OSMPolygon(SchemaBase):
    __tablename__ = 'osmpolygons'
    area_id = Column(BigInteger, primary_key=True)
    tags = Column(JSONB)
    geom = Column(Geometry(geometry_type='POLYGON', spatial_index=False))


# Use JSONB field for all datasets so we won't need migrations in the future

class FlickrPoint(SchemaBase):
    __tablename__ = 'flickrpoints'
    point_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', spatial_index=False))


class GTFSStop(SchemaBase):
    __tablename__ = 'gtfsstops'
    stop_id = Column(String, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', spatial_index=False))


# We usually have a completely different (denser) dataset of nodes for local
# accessibility. Makes no sense to save them in the same table as the OSM POIs.

class OSMAccessNode(SchemaBase):
    __tablename__ = 'osmaccessnodes'
    node_id = Column(BigInteger, primary_key=True)
    accessibilities = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', spatial_index=False))


class OoklaPoint(SchemaBase):
    __tablename__ = 'ooklapoints'
    quadkey_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', spatial_index=False))


class KonturPoint(SchemaBase):
    __tablename__ = 'konturpoints'
    hex_id = Column(BigInteger, primary_key=True)
    properties = Column(JSONB)
    geom = Column(Geometry(geometry_type='POINT', spatial_index=False))
