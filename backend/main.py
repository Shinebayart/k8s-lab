import os
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="User API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


class UserCreate(BaseModel):
    name: str
    email: str


# ── GET /users ────────────────────────────────────────────────
@app.get("/users")
def list_users():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name, email, created_at FROM users ORDER BY id;")
    rows = cur.fetchall()
    conn.close()
    return rows


# ── POST /users ───────────────────────────────────────────────
@app.post("/users", status_code=201)
def add_user(user: UserCreate):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at;",
            (user.name, user.email),
        )
        new_user = cur.fetchone()
        conn.commit()
        return new_user
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Email already exists.")
    finally:
        conn.close()


# ── DELETE /users/{id} ────────────────────────────────────────
@app.delete("/users/{user_id}", status_code=200)
def remove_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
    deleted = cur.fetchone()
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"deleted_id": user_id}


# ── GET /health ───────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
