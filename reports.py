import os
from pathlib import Path
import matplotlib.pyplot as plt

from db import get_connection, get_global_salary_cents
from db import fixed_total_for_month


APP_DIR = Path(os.getenv("APPDATA", ".")) / "ExpenseTracker"
REPORTS_DIR = APP_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def monthly_total(month_yyyy_mm: str) -> int:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(amount_cents), 0) AS total
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?;
        """, (month_yyyy_mm,)).fetchone()
    return int(row["total"])


def category_breakdown(month_yyyy_mm: str):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT category, SUM(amount_cents) AS total_cents
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?
            GROUP BY category
            ORDER BY total_cents DESC;
        """, (month_yyyy_mm,)).fetchall()
    return [(r["category"], int(r["total_cents"])) for r in rows]


def daily_totals(month_yyyy_mm: str):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT expense_date, SUM(amount_cents) AS total_cents
            FROM expenses
            WHERE substr(expense_date, 1, 7) = ?
            GROUP BY expense_date
            ORDER BY expense_date ASC;
        """, (month_yyyy_mm,)).fetchall()
    return [(r["expense_date"], int(r["total_cents"])) for r in rows]


def income_vs_spend(month_yyyy_mm: str):
    salary = get_global_salary_cents()
    variable = monthly_total(month_yyyy_mm)
    fixed = fixed_total_for_month(month_yyyy_mm)
    total_spend = variable + fixed
    net = salary - total_spend
    return salary, variable, fixed, total_spend, net



# -------- Chart generators (save to AppData/reports) --------

def save_category_pie(month_yyyy_mm: str) -> Path | None:
    data = category_breakdown(month_yyyy_mm)
    if not data:
        return None

    labels = [c for c, _ in data]
    values = [v / 100 for _, v in data]

    plt.figure()
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title(f"Spending by Category ({month_yyyy_mm})")

    out = REPORTS_DIR / f"{month_yyyy_mm}_category_pie.png"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return out


def save_daily_line(month_yyyy_mm: str) -> Path | None:
    data = daily_totals(month_yyyy_mm)
    if not data:
        return None

    dates = [d for d, _ in data]
    values = [v / 100 for _, v in data]

    plt.figure()
    plt.plot(dates, values, marker="o")
    plt.title(f"Daily Spending ({month_yyyy_mm})")
    plt.xlabel("Date")
    plt.ylabel("Amount ($)")
    plt.xticks(rotation=45)

    out = REPORTS_DIR / f"{month_yyyy_mm}_daily_line.png"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return out


def save_income_bar(month_yyyy_mm: str) -> Path:
    salary, spend, net = income_vs_spend(month_yyyy_mm)

    labels = ["Income", "Expenses", "Net"]
    values = [salary / 100, spend / 100, net / 100]

    plt.figure()
    plt.bar(labels, values)
    plt.title(f"Income vs Expenses ({month_yyyy_mm})")
    plt.ylabel("Amount ($)")

    out = REPORTS_DIR / f"{month_yyyy_mm}_income_vs_expenses.png"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return out

def combined_category_breakdown(month_yyyy_mm: str):
    # variable categories
    var = category_breakdown(month_yyyy_mm)

    # fixed categories grouped
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT category, COALESCE(SUM(amount_cents), 0) AS total_cents
            FROM fixed_expenses
            WHERE active = 1
              AND start_month <= ?
              AND (end_month IS NULL OR end_month >= ?)
            GROUP BY category
            ORDER BY total_cents DESC;
        """, (month_yyyy_mm, month_yyyy_mm)).fetchall()

    fixed = [(r["category"], int(r["total_cents"])) for r in rows]

    # merge
    merged = {}
    for c, v in var:
        merged[c] = merged.get(c, 0) + v
    for c, v in fixed:
        merged[c] = merged.get(c, 0) + v

    # sort desc
    return sorted(merged.items(), key=lambda x: x[1], reverse=True)
