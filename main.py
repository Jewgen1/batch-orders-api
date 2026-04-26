from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import psycopg
from psycopg.rows import dict_row
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Batch Orders API")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
Instrumentator().instrument(app).expose(app)


DB_HOST = os.getenv("DB_HOST", "batch-orders-db-rw")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "app")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

APP_VERSION = os.getenv("APP_VERSION", "local-dev")
POD_NAME = os.getenv("POD_NAME", "local")
NODE_NAME = os.getenv("NODE_NAME", "local")
POD_NAMESPACE = os.getenv("POD_NAMESPACE", "local")


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

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

        conn.commit()


@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception as e:
        print(f"WARNING: database initialization failed: {e}")


class OrderCreate(BaseModel):
    order_number: str


class OrderStatusUpdate(BaseModel):
    status: str

@app.get("/", response_class=HTMLResponse)
def portal(request: Request):
    return templates.TemplateResponse("portal.html", {"request": request})


@app.get("/meta")
def meta():
    db_status = "unknown"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "app": "batch-orders-api",
        "display_name": "Batch Operations Portal",
        "version": APP_VERSION,
        "pod_name": POD_NAME,
        "node_name": NODE_NAME,
        "namespace": POD_NAMESPACE,
        "db_status": db_status,
    }


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

@app.get("/events")
def list_events():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, event_type, message, created_at
                FROM events
                ORDER BY id DESC
                LIMIT 50
                """
            )
            rows = cur.fetchall()
    return rows


@app.post("/events/test")
def create_test_event():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events (event_type, message)
                VALUES (%s, %s)
                RETURNING id, event_type, message, created_at
                """,
                ("TEST_EVENT", "Test event generated from Batch Operations Portal"),
            )
            row = cur.fetchone()
        conn.commit()
    return row
