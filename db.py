import os
import sqlite3
from pathlib import Path
from typing import Optional, List

# App data folder (safe for installed apps)
APP_DIR = Path(os.getenv("APPDATA", ".")) / "ExpenseTracker"
APP_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = APP_DIR / "expenses.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,   -- 'YYYY-MM-DD'
                note TEXT
            );
        """)

        # Global settings table (salary stored here)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fixed_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                category TEXT NOT NULL,
                start_month TEXT NOT NULL,   -- 'YYYY-MM'
                end_month TEXT,              -- NULL means no end
                active INTEGER NOT NULL DEFAULT 1  -- 1 = active, 0 = inactive
            );
        """)


        conn.commit()


def add_expense(amount_cents: int, category: str, expense_date: str, note: Optional[str]):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO expenses (amount_cents, category, expense_date, note)
            VALUES (?, ?, ?, ?);
        """, (amount_cents, category, expense_date, note))
        conn.commit()


def list_expenses_for_month(month_yyyy_mm: str):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, amount_cents, category, expense_date, note
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?
            ORDER BY expense_date ASC, id ASC;
        """, (month_yyyy_mm,)).fetchall()
    return rows


def delete_expense(expense_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?;", (expense_id,))
        conn.commit()
        return cur.rowcount > 0


def list_months() -> List[str]:
    # Returns months like ["2025-12", "2025-11"]
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT DISTINCT substr(expense_date, 1, 7) AS month
            FROM expenses
            ORDER BY month DESC;
        """).fetchall()
    return [r["month"] for r in rows]


# ---------- Global Salary (stored as cents) ----------

def set_global_salary_cents(salary_cents: int):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES ('salary_cents', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        """, (str(salary_cents),))
        conn.commit()


def get_global_salary_cents() -> int:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT value FROM settings WHERE key = 'salary_cents';
        """).fetchone()
    return int(row["value"]) if row else 0

def add_fixed_expense(name: str, amount_cents: int, category: str, start_month: str, end_month: str | None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO fixed_expenses (name, amount_cents, category, start_month, end_month, active)
            VALUES (?, ?, ?, ?, ?, 1);
        """, (name, amount_cents, category, start_month, end_month))
        conn.commit()


def list_fixed_expenses():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, name, amount_cents, category, start_month, end_month, active
            FROM fixed_expenses
            ORDER BY active DESC, name ASC;
        """).fetchall()
    return rows


def delete_fixed_expense(fixed_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM fixed_expenses WHERE id = ?;", (fixed_id,))
        conn.commit()
        return cur.rowcount > 0


def set_fixed_active(fixed_id: int, is_active: bool):
    with get_connection() as conn:
        conn.execute("""
            UPDATE fixed_expenses
            SET active = ?
            WHERE id = ?;
        """, (1 if is_active else 0, fixed_id))
        conn.commit()


def fixed_total_for_month(month_yyyy_mm: str) -> int:
    # Applies fixed expenses that are active and within the date range
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(amount_cents), 0) AS total
            FROM fixed_expenses
            WHERE active = 1
              AND start_month <= ?
              AND (end_month IS NULL OR end_month >= ?);
        """, (month_yyyy_mm, month_yyyy_mm)).fetchone()
    return int(row["total"])
