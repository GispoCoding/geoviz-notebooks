import pytest
from pytest_postgresql import factories
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from models import OSMPoint
from scripts.import_osm import OsmImporter

postgres_external = factories.postgresql_noproc(port=5400, password="postgres")
postgres = factories.postgresql("postgres_external", dbname="test_osm_import")


@pytest.fixture(scope="function")
def db_engine(postgres):
    """SQLAlchemy DB engine for the test database."""
    engine = create_engine('postgresql+psycopg2://', creator=lambda: postgres.cursor().connection)
    yield engine


@pytest.fixture
def helsinki_importer(db_engine):
    """Setup a OsmImporter for Helsinki using the test database."""
    slug_string = "Helsinki"
    args = {
        "city": slug_string,
        "bbox": "24.82345, 60.14084, 25.06404, 60.29496",
    }

    helsinki_importer = OsmImporter(args)
    helsinki_importer._engine = db_engine.execution_options(
        schema_translate_map={"schema": slug_string}
    )

    yield helsinki_importer


def test_db_init(db_engine, helsinki_importer):
    """Test that an empty point table is created."""
    helsinki_importer._initialise_db()

    table_name = OSMPoint.__tablename__
    insp = inspect(db_engine)
    assert insp.has_table(table_name, schema=helsinki_importer.slug)
    columns = insp.get_columns(table_name, schema=helsinki_importer.slug)
    assert len(columns) == 3

    session = sessionmaker(bind=db_engine.execution_options(schema_translate_map={"schema": helsinki_importer.slug}))()
    assert session.query(OSMPoint).first() is None
    session.close()


def test_data_loading(db_engine, helsinki_importer):
    helsinki_importer.run()

    with db_engine.connect() as con:
        cur = con.execute("""select tags->'name', tags->'addr:city' from "Helsinki".osmpoints o where node_id = 25038585""")
        assert cur.fetchall() == [("Polyteekkarimuseo", "Espoo")]
