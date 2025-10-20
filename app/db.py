# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# Normalización defensiva de esquemas
if DATABASE_URL.startswith("postgres://"):
    # Heroku/Render suelen dar 'postgres://'
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    # A veces viene sin driver; añadimos psycopg
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql.psycopg://"):
    # Error típico: punto en lugar de '+'
    DATABASE_URL = DATABASE_URL.replace("postgresql.psycopg://", "postgresql+psycopg://", 1)

connect_args = {}
# (si usas SQLite local no hace falta ssl; para Postgres en Render no pongas connect_args raros)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
