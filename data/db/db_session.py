import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import URL
import os
from dotenv import dotenv_values

config = dotenv_values(".env")

SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init():
    global __factory

    if __factory:
        return

    conn_str = URL(
        'postgresql+psycopg2',
        username=config["POSTGRES_USERNAME"],
        password=config["POSTGRES_PASSWORD"],
        host=config["POSTGRES_HOST"],
        database=config["POSTGRES_DATABASE"],
        port=config["POSTGRES_PORT"],
        query={}
    )
    engine = sa.create_engine(conn_str, pool_size=0, max_overflow=0)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()