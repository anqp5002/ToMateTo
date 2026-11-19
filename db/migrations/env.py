"""One sync SQLAlchemy/Psycopg migration environment; URL comes from the caller."""

from alembic import context
from sqlalchemy import create_engine, pool
from tomateto.dataaccess.schema import metadata

from db.connection import database_url


def run_migrations() -> None:
    if context.is_offline_mode():
        context.configure(
            url=database_url(),
            target_metadata=metadata,
            literal_binds=True,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=metadata,
                compare_type=True,
                compare_server_default=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
