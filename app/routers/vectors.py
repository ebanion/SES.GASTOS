# app/routers/vectors.py
from __future__ import annotations
import os
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI

from ..db import get_db
from .. import models

logger = logging.getLogger("vectors")
router = APIRouter(prefix="/admin/vectors", tags=["vectors"])

# --- Seguridad ---
def require_internal_key(x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"), key: str | None = Query(default=None)):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

# --- Embeddings helper ---
try:
    client = OpenAI()
except Exception as e:
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not configured - Vector functionality disabled")
        client = None
    else:
        raise e

def embed_text(text: str) -> List[float]:
    if client is None:
        print("⚠️ OpenAI client not available - returning empty embedding")
        return []
    try:
        resp = client.embeddings.create(model="text-embedding-3-small", input=text[:3000])
        return resp.data[0].embedding
    except Exception as e:
        logger.exception("Error generando embedding:")
        raise HTTPException(status_code=500, detail=f"embedding_error: {e}")

# --- Inserta un vector (nuevo gasto) ---
@router.post("/insert", dependencies=[Depends(require_internal_key)])
def insert_vector(
    expense_id: str,
    apartment_id: str,
    text_snippet: str,
    vendor: str | None = None,
    category: str | None = None,
    vat_rate: float | None = None,
    db: Session = Depends(get_db),
):
    if client is None:
        raise HTTPException(status_code=503, detail="OpenAI API not configured - vector functionality disabled")
    emb = embed_text(text_snippet)
    q = text("""
        INSERT INTO expense_vectors (id, apartment_id, model, embedding, text_snippet, vendor, category, vat_rate)
        VALUES (:id, :apartment_id, :model, :embedding, :text_snippet, :vendor, :category, :vat_rate)
        ON CONFLICT (id) DO UPDATE SET
          embedding = EXCLUDED.embedding,
          text_snippet = EXCLUDED.text_snippet,
          vendor = EXCLUDED.vendor,
          category = EXCLUDED.category,
          vat_rate = EXCLUDED.vat_rate;
    """)
    try:
        db.execute(q, {
            "id": expense_id,
            "apartment_id": apartment_id,
            "model": "text-embedding-3-small",
            "embedding": emb,
            "text_snippet": text_snippet[:1000],
            "vendor": vendor,
            "category": category,
            "vat_rate": vat_rate,
        })
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Buscar facturas parecidas ---
@router.get("/search", dependencies=[Depends(require_internal_key)])
def search_vectors(
    apartment_id: str,
    query: str,
    k: int = 5,
    db: Session = Depends(get_db),
):
    if client is None:
        raise HTTPException(status_code=503, detail="OpenAI API not configured - vector functionality disabled")
    emb = embed_text(query)
    q = text("""
        SELECT id, vendor, category, vat_rate,
               1 - (embedding <=> :embedding) AS similarity
        FROM expense_vectors
        WHERE apartment_id = :apartment_id
        ORDER BY embedding <-> :embedding
        LIMIT :k;
    """)
    rows = db.execute(q, {"embedding": emb, "apartment_id": apartment_id, "k": k}).mappings().all()
    return [dict(r) for r in rows]

# --- Crear embeddings de facturas viejas (backfill) ---
@router.post("/backfill", dependencies=[Depends(require_internal_key)])
def backfill_vectors(apartment_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Expense)
    if apartment_id:
        q = q.filter(models.Expense.apartment_id == apartment_id)
    expenses = q.limit(2000).all()
    count = 0
    for e in expenses:
        text_snippet = f"{e.vendor or ''} {e.description or ''}"
        emb = embed_text(text_snippet)
        db.execute(text("""
            INSERT INTO expense_vectors (id, apartment_id, model, embedding, text_snippet, vendor, category, vat_rate)
            VALUES (:id, :apartment_id, :model, :embedding, :text_snippet, :vendor, :category, :vat_rate)
            ON CONFLICT (id) DO NOTHING;
        """), {
            "id": str(e.id),
            "apartment_id": str(e.apartment_id),
            "model": "text-embedding-3-small",
            "embedding": emb,
            "text_snippet": text_snippet[:1000],
            "vendor": e.vendor,
            "category": e.category,
            "vat_rate": e.vat_rate,
        })
        count += 1
        if count % 10 == 0:
            db.commit()
    db.commit()
    return {"inserted": count}
