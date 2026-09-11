from alembic import context
from app.config import settings
from app.database.models import Base
from app.database.session import make_engine

target_metadata = Base.metadata


def run_migrations():
    url = context.config.attributes.get("database_url", settings.database_url)
    if context.is_offline_mode():
        if not url:
            raise ValueError("DATABASE_URL is required")
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine = make_engine(url)
        try:
            with engine.connect() as connection:
                context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
                with context.begin_transaction():
                    context.run_migrations()
        finally:
            engine.dispose()


run_migrations()
