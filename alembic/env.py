from logging.config import fileConfig
from sqlalchemy import create_engine, pool, text
from alembic import context
import sys
import os

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.Base import Base
from app.models.Provider import Provider
from app.models.Run import Run
from app.models.RawData import RawData

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = os.getenv("FAST_API_DB_URL")

if not DATABASE_URL:
    raise ValueError("FAST_API_DB_URL is not set in .env file")

target_metadata = Base.metadata

def run_migrations_offline():
    """rin offline migrations"""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """run online migrations"""
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with engine.begin() as connection:
        connection.execute(text('CREATE SCHEMA IF NOT EXISTS raw_data'))
        connection.execute(text('CREATE SCHEMA IF NOT EXISTS processed_data'))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
