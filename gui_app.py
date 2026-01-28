# gui_app.py
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from db import (
    init_db,
    add_expense,
    delete_expense,
    list_expenses_for_month,
    list_months,
    set_global_salary_cents,
    get_global_salary_cents,
    add_fixed_expense,
    list_fixed_expenses,
    delete_fixed_expense,
    set_fixed_active,
)

from reports import (
    combined_category_breakdown,
    daily_totals,
    income_vs_spend,  # returns: salary, variable, fixed, total_spend, net
)


# ---------------- Helpers (money + date validation) ----------------

def money_to_cents_positive(s: str) -> int:
    s = s.strip()
    value = float(s)
    if value <= 0:
        raise ValueError("Amount must be > 0")
    return int(round(value * 100))


def money_to_cents_allow_zero(s: str) -> int:
    s = s.strip()
    if s == "":
        return 0
    value = float(s)
    if value < 0:
        raise ValueError("Amount must be >= 0")
    return int(round(value * 100))


def cents_to_money_str(cents: int) -> str:
    return f"{cents / 100:.2f}"


def validate_date(date_str: str) -> str:
    date_str = date_str.strip()
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def validate_month(month_str: str) -> str:
    month_str = month_str.strip()
    datetime.strptime(month_str, "%Y-%m")
    return month_str


def month_from_date(date_str: str) -> str:
    return date_str[:7]


# ---------------- GUI App ----------------

class ExpenseTrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("1200x700")

        init_db()

        self.selected_month = tk.StringVar()
        self.salary_var = tk.StringVar()

        self._build_ui()
        self._load_initial_state()

    # ---------- UI Layout ----------
    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_expenses = ttk.Frame(self.notebook)
        self.tab_fixed = ttk.Frame(self.notebook)
        self.tab_insights = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_expenses, text="Expenses")
        self.notebook.add(self.tab_fixed, text="Fixed Expenses")
        self.notebook.add(self.tab_insights, text="Insights")

        self._build_expenses_tab()
        self._build_fixed_tab()
        self._build_insights_tab()

    # ---------- Expenses Tab ----------
    def _build_expenses_tab(self):
        top = ttk.Frame(self.tab_expenses)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Month:").pack(side="left")
        self.month_combo = ttk.Combobox(
            top, textvariable=self.selected_month, width=12, state="readonly"
        )
        self.month_combo.pack(side="left", padx=8)
        self.month_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_all())

        ttk.Label(top, text="Global Salary ($):").pack(side="left", padx=(20, 0))
        self.salary_entry = ttk.Entry(top, textvariable=self.salary_var, width=12)
        self.salary_entry.pack(side="left", padx=8)
        ttk.Button(top, text="Save Salary", command=self.save_salary).pack(side="left")

        # Add expense form
        form = ttk.LabelFrame(self.tab_expenses, text="Add Expense")
        form.pack(fill="x", padx=10, pady=10)

        self.amount_e = ttk.Entry(form, width=12)
        self.category_e = ttk.Entry(form, width=18)
        self.date_e = ttk.Entry(form, width=14)
        self.note_e = ttk.Entry(form, width=50)

        ttk.Label(form, text="Amount ($)").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.amount_e.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(form, text="Category").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.category_e.grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=4, padx=6, pady=6, sticky="w")
        self.date_e.grid(row=0, column=5, padx=6, pady=6)

        ttk.Label(form, text="Note").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.note_e.grid(row=1, column=1, columnspan=5, padx=6, pady=6, sticky="we")

        form.columnconfigure(5, weight=1)

        ttk.Button(form, text="Add Expense", command=self.add_expense_clicked).grid(
            row=2, column=0, padx=6, pady=8, sticky="w"
        )

        # Expenses table
        table_frame = ttk.Frame(self.tab_expenses)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "date", "category", "amount", "note")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount ($)")
        self.tree.heading("note", text="Note")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("date", width=110)
        self.tree.column("category", width=160)
        self.tree.column("amount", width=120, anchor="e")
        self.tree.column("note", width=650)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btns = ttk.Frame(self.tab_expenses)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btns, text="Delete Selected Expense", command=self.delete_selected_expense).pack(side="left")

    # ---------- Fixed Expenses Tab ----------
    def _build_fixed_tab(self):
        form = ttk.LabelFrame(self.tab_fixed, text="Add Fixed Expense (recurs monthly)")
        form.pack(fill="x", padx=10, pady=10)

        self.fixed_name = ttk.Entry(form, width=20)
        self.fixed_amount = ttk.Entry(form, width=12)
        self.fixed_category = ttk.Entry(form, width=16)
        self.fixed_start = ttk.Entry(form, width=10)
        self.fixed_end = ttk.Entry(form, width=10)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.fixed_name.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(form, text="Amount ($)").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.fixed_amount.grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(form, text="Category").grid(row=0, column=4, padx=6, pady=6, sticky="w")
        self.fixed_category.grid(row=0, column=5, padx=6, pady=6)

        ttk.Label(form, text="Start (YYYY-MM)").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.fixed_start.grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(form, text="End (optional YYYY-MM)").grid(row=1, column=2, padx=6, pady=6, sticky="w")
        self.fixed_end.grid(row=1, column=3, padx=6, pady=6)

        ttk.Button(form, text="Add Fixed Expense", command=self.add_fixed_clicked).grid(
            row=2, column=0, padx=6, pady=8, sticky="w"
        )

        # Fixed table
        table_frame = ttk.Frame(self.tab_fixed)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "name", "category", "amount", "start", "end", "active")
        self.fixed_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)

        headings = [
            ("id", "ID", 60),
            ("name", "Name", 180),
            ("category", "Category", 150),
            ("amount", "Amount ($)", 120),
            ("start", "Start", 100),
            ("end", "End", 100),
            ("active", "Active", 90),
        ]
        for key, title, width in headings:
            self.fixed_tree.heading(key, text=title)
            self.fixed_tree.column(key, width=width)

        self.fixed_tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.fixed_tree.yview)
        self.fixed_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        btns = ttk.Frame(self.tab_fixed)
        btns.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btns, text="Toggle Active", command=self.toggle_fixed_active).pack(side="left")
        ttk.Button(btns, text="Delete Selected", command=self.delete_fixed_selected).pack(side="left", padx=10)

    # ---------- Insights Tab ----------
    def _build_insights_tab(self):
        top = ttk.Frame(self.tab_insights)
        top.pack(fill="x", padx=10, pady=10)

        self.summary_label = ttk.Label(top, text="", font=("Segoe UI", 11))
        self.summary_label.pack(side="left")

        charts = ttk.Frame(self.tab_insights)
        charts.pack(fill="both", expand=True, padx=10, pady=10)

        # Pie chart
        self.fig_pie = Figure(figsize=(4, 3), dpi=100)
        self.ax_pie = self.fig_pie.add_subplot(111)
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=charts)
        self.canvas_pie.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Line chart
        self.fig_line = Figure(figsize=(4, 3), dpi=100)
        self.ax_line = self.fig_line.add_subplot(111)
        self.canvas_line = FigureCanvasTkAgg(self.fig_line, master=charts)
        self.canvas_line.get_tk_widget().grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Bar chart
        self.fig_bar = Figure(figsize=(4, 3), dpi=100)
        self.ax_bar = self.fig_bar.add_subplot(111)
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=charts)
        self.canvas_bar.get_tk_widget().grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        for c in range(3):
            charts.columnconfigure(c, weight=1)
        charts.rowconfigure(0, weight=1)

    # ---------- Initial State ----------
    def _load_initial_state(self):
        months = list_months()
        current_month = datetime.now().strftime("%Y-%m")
        default_month = months[0] if months else current_month

        self._set_months_in_combo(default_month)

        # Salary load
        self.salary_var.set(cents_to_money_str(get_global_salary_cents()))

        # Default date for quick entry
        self.date_e.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Default fixed start month
        self.fixed_start.insert(0, current_month)

        self.refresh_all()

    def _set_months_in_combo(self, selected: str):
        months = list_months()
        current = datetime.now().strftime("%Y-%m")
        if current not in months:
            months = [current] + months

        self.month_combo["values"] = months
        self.selected_month.set(selected if selected in months else months[0])

    # ---------- Refresh / Update ----------
    def refresh_all(self):
        self.refresh_expenses_table()
        self.refresh_fixed_table()
        self.refresh_charts()

    def refresh_expenses_table(self):
        month = self.selected_month.get()
        rows = list_expenses_for_month(month)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rows:
            self.tree.insert("", "end", values=(
                r["id"],
                r["expense_date"],
                r["category"],
                f"{r['amount_cents'] / 100:.2f}",
                r["note"] or ""
            ))

    def refresh_fixed_table(self):
        for item in self.fixed_tree.get_children():
            self.fixed_tree.delete(item)

        rows = list_fixed_expenses()
        for r in rows:
            self.fixed_tree.insert("", "end", values=(
                r["id"],
                r["name"],
                r["category"],
                f"{r['amount_cents'] / 100:.2f}",
                r["start_month"],
                r["end_month"] or "",
                "Yes" if r["active"] == 1 else "No"
            ))

    def refresh_charts(self):
        month = self.selected_month.get()

        # Insights numbers (salary - (fixed + variable))
        salary, variable, fixed, total_spend, net = income_vs_spend(month)

        self.summary_label.config(
            text=(
                f"Month: {month}   "
                f"Income: ${salary/100:.2f}   "
                f"Fixed: ${fixed/100:.2f}   "
                f"Variable: ${variable/100:.2f}   "
                f"Total: ${total_spend/100:.2f}   "
                f"Net: ${net/100:.2f}"
            )
        )

        # PIE: combined categories (fixed + variable)
        self.ax_pie.clear()
        cat_data = combined_category_breakdown(month)
        if cat_data:
            labels = [c for c, _ in cat_data]
            values = [v / 100 for _, v in cat_data]
            self.ax_pie.pie(values, labels=labels, autopct="%1.1f%%")
            self.ax_pie.set_title("Spending by Category (Fixed + Variable)")
        else:
            self.ax_pie.text(0.5, 0.5, "No data", ha="center", va="center")
            self.ax_pie.set_title("Spending by Category")
        self.canvas_pie.draw()

        # LINE: daily totals (variable only)
        self.ax_line.clear()
        day_data = daily_totals(month)
        if day_data:
            dates = [d for d, _ in day_data]
            vals = [v / 100 for _, v in day_data]
            self.ax_line.plot(dates, vals, marker="o")
            self.ax_line.tick_params(axis="x", rotation=45)
            self.ax_line.set_title("Daily Variable Spending")
            self.ax_line.set_xlabel("Date")
            self.ax_line.set_ylabel("$")
        else:
            self.ax_line.text(0.5, 0.5, "No data", ha="center", va="center")
            self.ax_line.set_title("Daily Variable Spending")
        self.canvas_line.draw()

        # BAR: income vs expenses vs net (expenses = fixed + variable)
        self.ax_bar.clear()
        labels = ["Income", "Expenses", "Net"]
        values = [salary / 100, total_spend / 100, net / 100]
        self.ax_bar.bar(labels, values)
        self.ax_bar.set_title("Income vs Expenses")
        self.ax_bar.set_ylabel("$")
        self.canvas_bar.draw()

    # ---------- Actions: Expenses ----------
    def add_expense_clicked(self):
        try:
            amount_cents = money_to_cents_positive(self.amount_e.get())
            category = self.category_e.get().strip()
            if not category:
                raise ValueError("Category cannot be empty.")

            date = validate_date(self.date_e.get())
            note = self.note_e.get().strip() or None

            add_expense(amount_cents, category, date, note)

            # Clear amount/category/note (keep date)
            self.amount_e.delete(0, tk.END)
            self.category_e.delete(0, tk.END)
            self.note_e.delete(0, tk.END)

            # Update month selection if needed
            new_month = month_from_date(date)
            self._set_months_in_combo(new_month)

            self.refresh_all()

        except Exception as e:
            messagebox.showerror("Add Expense Error", str(e))

    def delete_selected_expense(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select an expense row first.")
            return

        item = self.tree.item(sel[0])
        expense_id = int(item["values"][0])

        if messagebox.askyesno("Confirm Delete", f"Delete expense ID {expense_id}?"):
            ok = delete_expense(expense_id)
            if ok:
                self._set_months_in_combo(self.selected_month.get())
                self.refresh_all()

    # ---------- Actions: Salary ----------
    def save_salary(self):
        try:
            salary_cents = money_to_cents_allow_zero(self.salary_var.get())
            set_global_salary_cents(salary_cents)
            self.refresh_charts()
            messagebox.showinfo("Salary", "Salary saved.")
        except Exception as e:
            messagebox.showerror("Salary Error", str(e))

    # ---------- Actions: Fixed Expenses ----------
    def add_fixed_clicked(self):
        try:
            name = self.fixed_name.get().strip()
            if not name:
                raise ValueError("Name cannot be empty.")

            amount_cents = money_to_cents_positive(self.fixed_amount.get())

            category = self.fixed_category.get().strip()
            if not category:
                raise ValueError("Category cannot be empty.")

            start = validate_month(self.fixed_start.get())

            end_raw = self.fixed_end.get().strip()
            end = validate_month(end_raw) if end_raw else None

            if end and end < start:
                raise ValueError("End month cannot be earlier than start month.")

            add_fixed_expense(name, amount_cents, category, start, end)

            self.fixed_name.delete(0, tk.END)
            self.fixed_amount.delete(0, tk.END)
            self.fixed_category.delete(0, tk.END)
            # keep start for convenience
            self.fixed_end.delete(0, tk.END)

            self.refresh_all()

        except Exception as e:
            messagebox.showerror("Fixed Expense Error", str(e))

    def toggle_fixed_active(self):
        sel = self.fixed_tree.selection()
        if not sel:
            messagebox.showinfo("Toggle", "Select a fixed expense first.")
            return

        item = self.fixed_tree.item(sel[0])
        fixed_id = int(item["values"][0])
        active_text = item["values"][6]
        is_active = True if active_text == "Yes" else False

        set_fixed_active(fixed_id, not is_active)
        self.refresh_all()

    def delete_fixed_selected(self):
        sel = self.fixed_tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a fixed expense first.")
            return

        item = self.fixed_tree.item(sel[0])
        fixed_id = int(item["values"][0])

        if messagebox.askyesno("Confirm Delete", f"Delete fixed expense ID {fixed_id}?"):
            delete_fixed_expense(fixed_id)
            self.refresh_all()


if __name__ == "__main__":
    app = ExpenseTrackerGUI()
    app.mainloop()
