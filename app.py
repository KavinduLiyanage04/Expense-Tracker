from datetime import datetime
from db import init_db, add_expense, list_expenses_for_month, delete_expense
from reports import monthly_total, category_breakdown, generate_category_pie_chart, generate_daily_line_chart


def money_to_cents(amount_str: str) -> int:
    # Converts "12.50" -> 1250 cents
    amount_str = amount_str.strip()
    dollars = float(amount_str)
    if dollars <= 0:
        raise ValueError("Amount must be > 0")
    return int(round(dollars * 100))


def ask_month() -> str:
    raw = input("Enter month (YYYY-MM), e.g., 2025-12: ").strip()
    datetime.strptime(raw, "%Y-%m")  # validate
    return raw


def ask_date() -> str:
    raw = input("Enter date (YYYY-MM-DD), e.g., 2025-12-28: ").strip()
    datetime.strptime(raw, "%Y-%m-%d")  # validate
    return raw


def print_expenses(rows):
    if not rows:
        print("No expenses found.")
        return

    print("\nID | Date       | Category        | Amount   | Note")
    print("-" * 60)
    for r in rows:
        amount = r["amount_cents"] / 100
        note = r["note"] or ""
        print(f'{r["id"]:>2} | {r["expense_date"]} | {r["category"]:<14} | ${amount:>7.2f} | {note}')


def main():
    init_db()

    while True:
        print("\n=== Expense Tracker ===")
        print("1) Add expense")
        print("2) View month summary")
        print("3) List expenses for a month")
        print("4) Delete expense by ID")
        print("5) Generate charts for a month")
        print("0) Exit")

        choice = input("Choose: ").strip()

        try:
            if choice == "1":
                amount_cents = money_to_cents(input("Amount ($): "))
                category = input("Category (e.g., Food, Transport): ").strip()
                if not category:
                    print("Category cannot be empty.")
                    continue

                expense_date = ask_date()
                note = input("Note (optional): ").strip() or None

                add_expense(amount_cents, category, expense_date, note)
                print("✅ Expense added!")

            elif choice == "2":
                month = ask_month()
                total_cents = monthly_total(month)
                breakdown = category_breakdown(month)

                print(f"\n--- Summary for {month} ---")
                print(f"Total spent: ${total_cents / 100:.2f}")

                if not breakdown:
                    print("No category data.")
                else:
                    print("\nBy category:")
                    for cat, cents in breakdown:
                        print(f"- {cat}: ${cents / 100:.2f}")

            elif choice == "3":
                month = ask_month()
                rows = list_expenses_for_month(month)
                print_expenses(rows)

            elif choice == "4":
                expense_id = int(input("Enter expense ID to delete: ").strip())
                if delete_expense(expense_id):
                    print("🗑️ Deleted.")
                else:
                    print("No expense found with that ID.")

            elif choice == "5":
                month = ask_month()
                pie = generate_category_pie_chart(month)
                line = generate_daily_line_chart(month)

                if not pie and not line:
                    print("No data for that month, no charts generated.")
                else:
                    if pie:
                        print(f"📊 Saved: {pie}")
                    if line:
                        print(f"📈 Saved: {line}")

            elif choice == "0":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Try again.")

        except ValueError as e:
            print(f"❌ Input error: {e}")


if __name__ == "__main__":
    main()
