# pytest: disable=redefined-outer-name
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from orm import metadata, start_mappers


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def mysql_db():
    engine = create_engine('mysql+mysqldb://root:123456@localhost:3306/test1')
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    db = in_memory_db
    start_mappers()
    yield sessionmaker(bind=db)()
    clear_mappers()
