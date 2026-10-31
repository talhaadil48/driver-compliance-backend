import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fix SSL root certificate path if pointing to a machine-specific or non-existent path
match = re.search(r'[?&]sslrootcert=([^&]+)', DATABASE_URL)
if match:
    cert_path = match.group(1)
    if not os.path.exists(cert_path):
        # 1. Try bundled certificate in certs/global-bundle.pem inside backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bundle_path = os.path.join(base_dir, 'certs', 'global-bundle.pem')
        if os.path.exists(bundle_path):
            DATABASE_URL = DATABASE_URL.replace(cert_path, bundle_path.replace("\\", "/"))
        else:
            # 2. Fall back to system trusted roots as suggested by psycopg
            DATABASE_URL = DATABASE_URL.replace(cert_path, "system")

# Optimized connect arguments and connection pool
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # On Serverless platforms like Vercel, use NullPool to avoid connection pool exhaustion
    if os.environ.get("VERCEL") == "1":
        from sqlalchemy.pool import NullPool
        engine_kwargs["poolclass"] = NullPool
    else:
        # Persistent connection pooling for dedicated/local server
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 1800,
            "pool_timeout": 30,
        })

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

# For PostgreSQL, ensure dedicated schema exists on initial start
if DATABASE_URL.startswith("postgresql"):
    try:
        with engine.connect() as connection:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.DB_SCHEMA};"))
            connection.commit()
    except Exception as e:
        print(f"[Database Init Warning] Could not create schema '{settings.DB_SCHEMA}': {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
