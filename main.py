from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg
from psycopg.rows import dict_row

app = FastAPI(title="Batch Orders API")


DB_HOST = os.getenv("DB_HOST", "batch-orders-db-rw")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "app")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_conn():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row,
    )


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    order_number TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        conn.commit()


@app.on_event("startup")
def startup():
    init_db()


class OrderCreate(BaseModel):
    order_number: str


class OrderStatusUpdate(BaseModel):
    status: str


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders")
def list_orders():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, order_number, status, created_at
                FROM orders
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return rows


@app.post("/orders")
def create_order(order: OrderCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO orders (order_number, status)
                    VALUES (%s, %s)
                    RETURNING id, order_number, status, created_at
                    """,
                    (order.order_number, "NEW"),
                )
                row = cur.fetchone()
            conn.commit()
        return row
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="order_number already exists")


@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, payload: OrderStatusUpdate):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orders
                SET status = %s
                WHERE id = %s
                RETURNING id, order_number, status, created_at
                """,
                (payload.status, order_id),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=404, detail="order not found")

    return row
