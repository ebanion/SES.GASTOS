# app/db.py
from __future__ import annotations
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# --- Normalización robusta de driver para Postgres ---
try:
    url = make_url(DATABASE_URL)

    # Heroku/Render a veces dan 'postgres://'
    if url.drivername == "postgres":
        url = url.set(drivername="postgresql+psycopg")

    # Si viene sin driver (postgresql://...), añade psycopg
    elif url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")

    # Error típico: 'postgresql.psycopg' con punto en vez de '+'
    elif url.drivername == "postgresql.psycopg":
        url = url.set(drivername="postgresql+psycopg")

    # Aplica cambios
    DATABASE_URL = str(url)

except Exception:
    # Fallback muy defensivo si no ha podido parsear
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql.psycopg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql.psycopg://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Log (sin password) para verificar en Render qué driver quedó
masked = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] Using DATABASE_URL = {masked}")

connect_args = {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
