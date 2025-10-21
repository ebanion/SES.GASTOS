# app/db.py
from __future__ import annotations
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url
from sqlalchemy.exc import NoSuchModuleError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# --- Normalización a psycopg (psycopg3) ---
try:
    url = make_url(DATABASE_URL)
    if url.drivername == "postgres":
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername == "postgresql.psycopg":  # error común con '.'
        url = url.set(drivername="postgresql+psycopg")
    DATABASE_URL = str(url)
except Exception:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql.psycopg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql.psycopg://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

masked = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] Using DATABASE_URL = {masked}")

connect_args = {}
engine = None

# --- Intento 1: psycopg (psycopg3) ---
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
except NoSuchModuleError as e:
    # Si el plugin 'postgresql.psycopg' no existe, caemos a psycopg2
    if "postgresql.psycopg" in str(e):
        print("[DB] psycopg dialect not found — falling back to postgresql+psycopg2")
        try:
            alt_url = str(make_url(DATABASE_URL).set(drivername="postgresql+psycopg2"))
        except Exception:
            alt_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
        DATABASE_URL = alt_url
        masked = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
        print(f"[DB] Fallback DATABASE_URL = {masked}")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


